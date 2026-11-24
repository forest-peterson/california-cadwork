#!/usr/bin/env python3
"""Critical path calculation and float blocks for a Primavera P6 XML schedule.

Runs the forward and backward pass from the file's logic, durations and
calendars, checks the result against the dates P6 stored in the file, groups
activities into blocks by total float, and splits each block into fragments
(members of the block linked to one another by logic).

Usage:
    python cpm_blocks.py SCHEDULE.xml --summary          one line per block
    python cpm_blocks.py SCHEDULE.xml --block 5          one block in detail
    python cpm_blocks.py SCHEDULE.xml                    every block, every activity
Options:
    --project ID            choose a project when the file holds several
    --csv OUT.csv           also write one row per activity
    --base-exceptions ignore   use each calendar's own exceptions only
                               (default merges in its base calendar's exceptions)

Exit status 2 means the schedule uses something this script does not model;
the message says what, because float computed without it would be wrong.
"""
import argparse
import csv
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque

MINUTE = dt.timedelta(minutes=1)
DAYS = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
        'Friday': 4, 'Saturday': 5, 'Sunday': 6}
MAX_SCAN_DAYS = 40000
REL_TYPES = {'Finish to Start': 'FS', 'Start to Start': 'SS',
             'Finish to Finish': 'FF', 'Start to Finish': 'SF'}
CONSTRAINTS_MODELED = {'Start On', 'Start On or After', 'Start On or Before',
                       'Finish On', 'Finish On or After', 'Finish On or Before'}
NETWORK_TYPES = {'Task Dependent', 'Resource Dependent', 'Start Milestone', 'Finish Milestone'}


class Unsupported(Exception):
    """The schedule uses a feature this script does not model."""


# ---------------------------------------------------------------- XML helpers

def strip_namespaces(root):
    for el in root.iter():
        el.tag = el.tag.rsplit('}', 1)[-1]
        for key in list(el.attrib):
            if '}' in key:
                el.attrib[key.rsplit('}', 1)[-1]] = el.attrib.pop(key)
    return root


def text(el, tag):
    value = el.findtext(tag)
    return value.strip() if value else ''


def is_nil(el):
    return el.get('nil') == 'true'


def when(value):
    return dt.datetime.fromisoformat(value) if value else None


def clock(value, finish=False):
    h, m = (int(x) for x in value.split(':')[:2])
    t = h * 60 + m
    # P6 XML writes the last working minute of a period (16:59 means work runs to 17:00).
    if finish and (m + 1) % 30 == 0:
        t += 1
    return t


# ---------------------------------------------------------------- calendars

class Calendar:
    def __init__(self, cid, name, hours_per_day, week, exceptions):
        self.id, self.name, self.hours_per_day = cid, name, hours_per_day
        self.week = week                  # weekday -> [(start_minute, end_minute)]
        self.exceptions = exceptions      # date -> [(start_minute, end_minute)], [] = no work
        self._cache = {}

    def periods(self, day):
        if day not in self._cache:
            spans = self.exceptions.get(day, self.week[day.weekday()])
            base = dt.datetime.combine(day, dt.time())
            self._cache[day] = [(base + s * MINUTE, base + e * MINUTE) for s, e in spans]
        return self._cache[day]

    def _forward(self, t):
        day = t.date()
        for i in range(MAX_SCAN_DAYS):
            for s, e in self.periods(day + dt.timedelta(days=i)):
                if e > t:
                    yield s, e
        raise Unsupported(f'calendar "{self.name}" has no working time after {t:%Y-%m-%d}')

    def _backward(self, t):
        day = t.date()
        for i in range(MAX_SCAN_DAYS):
            for s, e in reversed(self.periods(day - dt.timedelta(days=i))):
                if s < t:
                    yield s, e
        raise Unsupported(f'calendar "{self.name}" has no working time before {t:%Y-%m-%d}')

    def next_start(self, t):
        """Earliest instant at or after t at which work can begin."""
        for s, _ in self._forward(t):
            return max(s, t)

    def prev_end(self, t):
        """Latest instant at or before t at which work can end."""
        for _, e in self._backward(t):
            return min(e, t)

    def is_start_point(self, t):
        return any(s <= t < e for s, e in self.periods(t.date()))

    def is_finish_point(self, t):
        return any(s < t <= e for s, e in self.periods(t.date())) or \
            any(s < t <= e for s, e in self.periods(t.date() - dt.timedelta(days=1)))

    def add(self, t, mins):
        if mins <= 0:
            return self.sub(t, -mins) if mins < 0 else t
        for s, e in self._forward(t):
            b = max(s, t)
            room = (e - b) / MINUTE
            if mins <= room:
                return b + mins * MINUTE
            mins -= room

    def sub(self, t, mins):
        if mins <= 0:
            return self.add(t, -mins) if mins < 0 else t
        for s, e in self._backward(t):
            end = min(e, t)
            room = (end - s) / MINUTE
            if mins <= room:
                return end - mins * MINUTE
            mins -= room

    def between(self, t1, t2):
        """Working minutes from t1 to t2 (negative when t2 is earlier)."""
        if t2 < t1:
            return -self.between(t2, t1)
        total = 0.0
        for s, e in self._forward(t1):
            if s >= t2:
                break
            b, end = max(s, t1), min(e, t2)
            if end > b:
                total += (end - b) / MINUTE
        return total


def read_calendars(root, project, merge_base):
    elements = {}
    for el in list(root.findall('Calendar')) + list(project.findall('Calendar')):
        elements[text(el, 'ObjectId')] = el
    built = {}

    def build(cid, trail=()):
        if cid in built:
            return built[cid]
        if cid not in elements:
            raise Unsupported(f'calendar ObjectId {cid} is referenced but not in the file')
        el = elements[cid]
        week = {i: [] for i in range(7)}
        sww = el.find('StandardWorkWeek')
        for d in (sww.findall('StandardWorkHours') if sww is not None else []):
            for w in d.findall('WorkTime'):
                if not is_nil(w) and text(w, 'Start'):
                    week[DAYS[text(d, 'DayOfWeek')]].append(
                        (clock(text(w, 'Start')), clock(text(w, 'Finish'), True)))
        exceptions = {}
        base_id = text(el, 'BaseCalendarObjectId')
        if merge_base and base_id and base_id not in trail:
            exceptions.update(build(base_id, trail + (cid,)).exceptions)
        hol = el.find('HolidayOrExceptions')
        for h in (hol.findall('HolidayOrException') if hol is not None else []):
            day = dt.date.fromisoformat(text(h, 'Date')[:10])
            exceptions[day] = [(clock(text(w, 'Start')), clock(text(w, 'Finish'), True))
                               for w in h.findall('WorkTime') if not is_nil(w) and text(w, 'Start')]
        cal = Calendar(cid, text(el, 'Name'), float(text(el, 'HoursPerDay') or 8), week, exceptions)
        built[cid] = cal
        return cal

    for cid in elements:
        build(cid)
    return built


# ---------------------------------------------------------------- schedule model

def option(opts, name, default=''):
    if opts is None:
        return default
    value = text(opts, name)
    return value if value else default


def load(path, project_id=None, merge_base=True):
    root = strip_namespaces(ET.parse(path).getroot())
    projects = root.findall('Project')
    if not projects:
        raise Unsupported('no Project element in the file')
    if project_id:
        projects = [p for p in projects if text(p, 'Id') == project_id]
        if not projects:
            raise Unsupported(f'no project with Id {project_id}')
    elif len(projects) > 1:
        ids = ', '.join(text(p, 'Id') for p in projects)
        raise Unsupported(f'the file holds several projects ({ids}); choose one with --project')
    proj = projects[0]
    cals = read_calendars(root, proj, merge_base)
    opts = proj.find('ScheduleOptions')
    notes = []

    float_type = option(opts, 'ComputeTotalFloatType', 'Finish Float = Late Finish - Early Finish')
    if float_type.startswith('Finish Float'):
        float_rule = 'finish'
    elif float_type.startswith('Start Float'):
        float_rule = 'start'
    elif float_type.startswith('Smallest'):
        float_rule = 'smallest'
    else:
        raise Unsupported(f'total float setting "{float_type}"')

    lag_setting = option(opts, 'RelationshipLagCalendar', 'Predecessor Activity Calendar')
    default_cal = cals.get(text(proj, 'ActivityDefaultCalendarObjectId'))
    if lag_setting.startswith('Predecessor'):
        lag_rule = 'predecessor'
    elif lag_setting.startswith('Successor'):
        lag_rule = 'successor'
    elif lag_setting.startswith('24'):
        lag_rule = 'fixed'
        default_cal = Calendar('24h', '24 hour', 24.0, {i: [(0, 1440)] for i in range(7)}, {})
    elif lag_setting.startswith('Project Default'):
        lag_rule = 'fixed'
        if default_cal is None:
            raise Unsupported('lags use the project default calendar, but the project names none')
    else:
        raise Unsupported(f'relationship lag calendar setting "{lag_setting}"')

    if option(opts, 'UseExpectedFinishDates', '0') == '1' and \
            any(text(a, 'ExpectedFinishDate') for a in proj.findall('Activity')):
        raise Unsupported('the schedule uses expected finish dates')
    if option(opts, 'LevelResourcesDuringScheduling', '0') == '1':
        notes.append('P6 levels resources during scheduling for this project; leveled dates will not match CPM dates')

    acts, excluded = {}, defaultdict(list)
    for a in proj.findall('Activity'):
        kind, status = text(a, 'Type'), text(a, 'Status')
        rec = dict(oid=text(a, 'ObjectId'), id=text(a, 'Id'), name=text(a, 'Name'), type=kind,
                   status=status, wbs=text(a, 'WBSObjectId'))
        if status == 'Completed':
            excluded['completed'].append(rec)
            continue
        if status == 'In Progress':
            excluded['in progress'].append(rec)
            continue
        if kind not in NETWORK_TYPES:
            excluded[kind or 'unknown type'].append(rec)
            continue
        cid = text(a, 'CalendarObjectId')
        if cid not in cals:
            raise Unsupported(f'activity {rec["id"]} uses calendar ObjectId {cid}, which is not in the file')
        constraints = []
        for kind_tag, date_tag in (('PrimaryConstraintType', 'PrimaryConstraintDate'),
                                   ('SecondaryConstraintType', 'SecondaryConstraintDate')):
            ctype = text(a, kind_tag)
            if ctype:
                if ctype not in CONSTRAINTS_MODELED:
                    raise Unsupported(f'activity {rec["id"]} has a "{ctype}" constraint')
                constraints.append((ctype, when(text(a, date_tag))))
        duration = 0.0 if 'Milestone' in kind else float(text(a, 'RemainingDuration') or 0) * 60
        rec.update(cal=cals[cid], dur=duration, constraints=constraints,
                   p6=dict(ES=when(text(a, 'RemainingEarlyStartDate')),
                           EF=when(text(a, 'RemainingEarlyFinishDate')),
                           LS=when(text(a, 'RemainingLateStartDate')),
                           LF=when(text(a, 'RemainingLateFinishDate'))))
        acts[rec['oid']] = rec

    if excluded['in progress']:
        raise Unsupported(f'{len(excluded["in progress"])} activities are in progress; '
                          'progress (actual dates and retained logic or progress override) is not modeled')

    resource_dependent = {k for k, a in acts.items() if a['type'] == 'Resource Dependent'}
    assigned = {text(r, 'ActivityObjectId') for r in proj.findall('ResourceAssignment')}
    if resource_dependent & assigned:
        notes.append('resource-dependent activities have resources assigned; resource calendars are not used here')

    other = {r['oid'] for kind, recs in excluded.items() if kind != 'completed' for r in recs}
    completed = {r['oid'] for r in excluded['completed']}
    rels = []
    for r in proj.findall('Relationship'):
        p, s = text(r, 'PredecessorActivityObjectId'), text(r, 'SuccessorActivityObjectId')
        rtype = REL_TYPES.get(text(r, 'Type'))
        if rtype is None:
            raise Unsupported(f'relationship type "{text(r, "Type")}"')
        if p in other or s in other:
            raise Unsupported('level-of-effort or WBS summary activities carry logic, which is not modeled')
        if p in acts and s in acts:
            rels.append(dict(p=p, s=s, type=rtype, lag=float(text(r, 'Lag') or 0) * 60))
        elif not ({p, s} & completed):
            notes.append(f'relationship {p}->{s} reaches outside this project and was ignored')

    info = dict(id=text(proj, 'Id'), name=text(proj, 'Name'),
                data_date=when(text(proj, 'DataDate')) or when(text(proj, 'PlannedStartDate')),
                must_finish=when(text(proj, 'MustFinishByDate')),
                float_rule=float_rule, float_setting=float_type, lag_rule=lag_rule,
                lag_setting=lag_setting, lag_cal=default_cal,
                open_ended_critical=option(opts, 'MakeOpenEndedActivitiesCritical', '0') == '1',
                excluded=excluded, notes=notes, merge_base=merge_base)
    if info['data_date'] is None:
        raise Unsupported('the project has no data date or planned start')
    return acts, rels, info


# ---------------------------------------------------------------- CPM

def schedule(acts, rels, info):
    preds, succs = defaultdict(list), defaultdict(list)
    for r in rels:
        preds[r['s']].append(r)
        succs[r['p']].append(r)
    indegree = {k: len(preds[k]) for k in acts}
    queue = deque(sorted((k for k in acts if indegree[k] == 0), key=lambda k: acts[k]['id']))
    order = []
    while queue:
        k = queue.popleft()
        order.append(k)
        for r in succs[k]:
            indegree[r['s']] -= 1
            if indegree[r['s']] == 0:
                queue.append(r['s'])
    if len(order) < len(acts):
        loop = sorted(acts[k]['id'] for k in acts if indegree[k] > 0)
        raise Unsupported('the logic has a loop through ' + ', '.join(loop[:12]))

    warnings = info['notes']

    def lag_cal(r):
        if info['lag_rule'] == 'predecessor':
            return acts[r['p']]['cal']
        if info['lag_rule'] == 'successor':
            return acts[r['s']]['cal']
        return info['lag_cal']

    # forward pass
    for k in order:
        a, c = acts[k], acts[k]['cal']
        finish_ms, start_ms = a['type'] == 'Finish Milestone', a['type'] == 'Start Milestone'
        es = c.next_start(info['data_date'])
        floor = None                                   # earliest allowed finish

        def raise_floor(t):
            nonlocal floor
            floor = t if floor is None else max(floor, t)

        for r in preds[k]:
            p, lc = acts[r['p']], lag_cal(r)
            if r['type'] in ('FS', 'FF'):
                t = lc.add(p['EF'], r['lag'])
            else:
                t = lc.add(p['ES'], r['lag'])
            if r['type'] in ('FS', 'SS') and not finish_ms:
                es = max(es, c.next_start(t))
            else:
                raise_floor(t)
        for ctype, date in a['constraints']:
            if ctype in ('Start On', 'Start On or After'):
                if finish_ms:
                    raise_floor(date)
                else:
                    es = max(es, c.next_start(date))
            if ctype in ('Finish On', 'Finish On or After'):
                raise_floor(date)
        if finish_ms:
            ef = es if floor is None else floor
            if not c.is_finish_point(ef):
                warnings.append(f'{a["id"]}: finish milestone falls in nonwork time; moved to the next work period')
                ef = c.next_start(ef)
            a['ES'] = a['EF'] = ef
            continue
        if floor is not None:
            if start_ms:
                es = max(es, c.next_start(floor))
            else:
                in_nonwork = False
                if c.is_start_point(floor) and not c.is_finish_point(floor):
                    floor = c.prev_end(floor)          # a period start is the same work position as the last period end
                elif not c.is_finish_point(floor):
                    in_nonwork = True
                    floor = c.next_start(floor)
                candidate = c.next_start(c.sub(floor, a['dur']))
                if in_nonwork and candidate > es:
                    warnings.append(f'{a["id"]}: a finish link lands in nonwork time on its calendar and sets '
                                    'its early dates; compare this activity with P6')
                es = max(es, candidate)
        a['ES'] = es
        a['EF'] = c.add(es, a['dur'])

    # backward pass
    project_finish = info['must_finish'] or max(acts[k]['EF'] for k in order)
    for k in reversed(order):
        a, c = acts[k], acts[k]['cal']
        start_ms, finish_ms = a['type'] == 'Start Milestone', a['type'] == 'Finish Milestone'
        if not succs[k] and info['open_ended_critical']:
            lf = a['EF']
        else:
            lf = c.prev_end(project_finish)
        ceiling = None                                 # latest allowed start
        for r in succs[k]:
            s, lc = acts[r['s']], lag_cal(r)
            if r['type'] in ('FS', 'SS'):
                t = lc.sub(s['LS'], r['lag'])
            else:
                t = lc.sub(s['LF'], r['lag'])
            if r['type'] in ('FS', 'FF'):
                lf = min(lf, c.prev_end(t))
            else:
                ceiling = t if ceiling is None else min(ceiling, t)
        for ctype, date in a['constraints']:
            if ctype in ('Start On', 'Start On or Before'):
                ceiling = date if ceiling is None else min(ceiling, date)
            if ctype in ('Finish On', 'Finish On or Before'):
                lf = min(lf, c.prev_end(date))
        if ceiling is not None:
            candidate = c.add(ceiling, a['dur']) if a['dur'] else ceiling
            if a['dur'] and candidate < lf and not c.is_start_point(ceiling):
                warnings.append(f'{a["id"]}: a start link lands in nonwork time on its calendar and sets '
                                'its late dates; compare this activity with P6')
            lf = min(lf, candidate)
        if start_ms:
            a['LS'] = a['LF'] = c.next_start(lf)
        elif finish_ms:
            a['LS'] = a['LF'] = lf
        else:
            a['LF'] = lf
            a['LS'] = c.next_start(c.sub(lf, a['dur']))

    # float
    def total_float(c, es, ef, ls, lf, kind):
        start_f, finish_f = c.between(es, ls), c.between(ef, lf)
        if kind == 'Start Milestone':
            finish_f = start_f
        if kind == 'Finish Milestone':
            start_f = finish_f
        rule = info['float_rule']
        return finish_f if rule == 'finish' else start_f if rule == 'start' else min(start_f, finish_f)

    for k in order:
        a, c = acts[k], acts[k]['cal']
        a['TF'] = total_float(c, a['ES'], a['EF'], a['LS'], a['LF'], a['type']) / 60
        slack = None
        for r in succs[k]:
            s, lc = acts[r['s']], lag_cal(r)
            if r['type'] == 'FS':
                room = c.between(a['EF'], lc.sub(s['EF'] if s['type'] == 'Finish Milestone' else s['ES'], r['lag']))
            elif r['type'] == 'SS':
                room = c.between(a['ES'], lc.sub(s['ES'], r['lag']))
            elif r['type'] == 'FF':
                room = c.between(a['EF'], lc.sub(s['EF'], r['lag']))
            else:
                room = c.between(a['ES'], lc.sub(s['EF'], r['lag']))
            slack = room if slack is None else min(slack, room)
        if slack is None:                              # open end: measured to the project finish
            slack = c.between(a['EF'], c.prev_end(project_finish))
        a['FF'] = max(slack, 0.0) / 60
        p6 = a['p6']
        if all(p6.values()):
            a['TF_p6'] = total_float(c, p6['ES'], p6['EF'], p6['LS'], p6['LF'], a['type']) / 60
    return order, preds, succs, warnings


# ---------------------------------------------------------------- blocks and fragments

def days(a, hours):
    return round(hours / a['cal'].hours_per_day, 2) + 0.0      # + 0.0 turns -0.0 into 0.0


def label(x):
    return f'{x:g}'


def blocks_and_fragments(acts, rels, order):
    blocks = defaultdict(list)
    for k in order:
        a = acts[k]
        a['tf_days'], a['ff_days'] = days(a, a['TF']), days(a, a['FF'])
        blocks[a['tf_days']].append(k)
    result = {}
    for value, members in blocks.items():
        member_set = set(members)
        links = defaultdict(set)
        for r in rels:
            if r['p'] in member_set and r['s'] in member_set:
                links[r['p']].add(r['s'])
                links[r['s']].add(r['p'])
        seen, fragments = set(), []
        for m in sorted(members, key=lambda k: (acts[k]['ES'], acts[k]['id'])):
            if m in seen:
                continue
            stack, piece = [m], []
            seen.add(m)
            while stack:
                x = stack.pop()
                piece.append(x)
                for y in links[x] - seen:
                    seen.add(y)
                    stack.append(y)
            fragments.append(sorted(piece, key=lambda k: (acts[k]['ES'], acts[k]['id'])))
        result[value] = fragments
        for i, piece in enumerate(fragments, 1):
            for k in piece:
                acts[k]['fragment'] = i
    return result


def check_against_p6(acts, order):
    checked = [k for k in order if 'TF_p6' in acts[k]]
    differ = []
    for k in checked:
        a = acts[k]
        fields = [f for f in ('ES', 'EF', 'LS', 'LF') if a[f] != a['p6'][f]]
        if abs(a['TF'] - a['TF_p6']) > 1e-6:
            fields.append('total float')
        if fields:
            differ.append((a, fields))
    return checked, differ


# ---------------------------------------------------------------- report

def stamp(t):
    return f'{t:%Y-%m-%d %H:%M}'


def report(acts, rels, info, order, succs, warnings, blocks, args):
    out = []
    out.append(f'Project {info["id"]}: {info["name"]}')
    out.append(f'Data date {stamp(info["data_date"])}'
               + (f'; must finish by {stamp(info["must_finish"])}' if info['must_finish'] else ''))
    out.append(f'Total float: {info["float_setting"]}. Lags on: {info["lag_setting"]}. '
               f'Open-ended activities critical: {"yes" if info["open_ended_critical"] else "no"}.')
    skipped = ', '.join(f'{len(v)} {k}' for k, v in info['excluded'].items() if v)
    out.append(f'Analyzed {len(order)} activities' + (f' (not analyzed: {skipped})' if skipped else '') + '.')
    checked, differ = check_against_p6(acts, order)
    if not checked:
        out.append('Check against P6: the file carries no P6-calculated dates, so the result is unchecked.')
    elif not differ:
        out.append(f'Check against P6: all {len(checked)} activities match P6\'s stored early and late '
                   'dates and total float.')
    else:
        out.append(f'Check against P6: {len(checked) - len(differ)} of {len(checked)} match; '
                   f'{len(differ)} differ:')
        for a, fields in differ[:25]:
            out.append(f'  {a["id"]} {a["name"][:40]}: {", ".join(fields)}')
        if len(differ) > 25:
            out.append(f'  ... and {len(differ) - 25} more')
    out.append('Float is in days of each activity\'s own calendar (hours divided by that calendar\'s hours per day).')
    for w in dict.fromkeys(warnings):
        out.append(f'Warning: {w}')
    out.append('')

    def exits(piece, value):
        lines = []
        members = set(piece)
        for k in piece:
            for r in succs[k]:
                if r['s'] not in members:
                    s = acts[r['s']]
                    lines.append(f'    feeds {s["id"]} ({s["name"][:30]}) in block {label(s["tf_days"])} '
                                 f'from {acts[k]["id"]}')
        return lines

    values = sorted(blocks)
    if args.block is not None:
        if args.block not in blocks:
            out.append(f'No block {label(args.block)}. Blocks present: {", ".join(label(v) for v in values)}')
            return '\n'.join(out)
        values = [args.block]
    for value in values:
        fragments = blocks[value]
        count = sum(len(p) for p in fragments)
        first = min(acts[k]['ES'] for p in fragments for k in p)
        last = max(acts[k]['EF'] for p in fragments for k in p)
        out.append(f'Block {label(value)}: {count} activit{"y" if count == 1 else "ies"}, '
                   f'{len(fragments)} fragment{"" if len(fragments) == 1 else "s"}, '
                   f'{first:%Y-%m-%d} to {last:%Y-%m-%d}')
        if args.summary:
            continue
        for i, piece in enumerate(fragments, 1):
            out.append(f'  Fragment {i} ({len(piece)}):')
            for k in piece:
                a = acts[k]
                line = (f'    {a["id"]:<12} {a["name"][:40]:<40} ES {a["ES"]:%Y-%m-%d}  EF {a["EF"]:%Y-%m-%d}  '
                        f'FF {label(a["ff_days"])}')
                if args.block is not None:
                    line += f'  LS {a["LS"]:%Y-%m-%d}  LF {a["LF"]:%Y-%m-%d}  [{a["cal"].name}]'
                out.append(line)
            if args.block is not None:
                out.extend(exits(piece, value))
    return '\n'.join(out)


def write_csv(path, acts, order):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['activity_id', 'name', 'type', 'calendar', 'early_start', 'early_finish',
                    'late_start', 'late_finish', 'total_float_days', 'free_float_days', 'block', 'fragment'])
        for k in sorted(order, key=lambda k: (acts[k]['tf_days'], acts[k].get('fragment', 0), acts[k]['ES'])):
            a = acts[k]
            w.writerow([a['id'], a['name'], a['type'], a['cal'].name, stamp(a['ES']), stamp(a['EF']),
                        stamp(a['LS']), stamp(a['LF']), label(a['tf_days']), label(a['ff_days']),
                        label(a['tf_days']), a.get('fragment', '')])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('schedule')
    ap.add_argument('--project')
    group = ap.add_mutually_exclusive_group()
    group.add_argument('--summary', action='store_true')
    group.add_argument('--block', type=float)
    ap.add_argument('--csv')
    ap.add_argument('--base-exceptions', choices=('merge', 'ignore'), default='merge')
    args = ap.parse_args()
    try:
        acts, rels, info = load(args.schedule, args.project, args.base_exceptions == 'merge')
        order, preds, succs, warnings = schedule(acts, rels, info)
    except Unsupported as e:
        print(f"Can't compute float for this schedule: {e}.")
        sys.exit(2)
    blocks = blocks_and_fragments(acts, rels, order)
    if args.block is not None:
        args.block = round(args.block, 2)
    print(report(acts, rels, info, order, succs, warnings, blocks, args))
    if args.csv:
        write_csv(args.csv, acts, order)
        print(f'\nWrote {args.csv}')


if __name__ == '__main__':
    main()
