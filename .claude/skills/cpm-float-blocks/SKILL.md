---
name: cpm-float-blocks
description: Read a CPM schedule through its float blocks. Computes early and late dates and total and free float from a schedule network, groups activities into blocks named by their total float value (block 5 is every activity with 5 days of total float, block 0 is the critical work), and checks whether each block is one fragment of linked logic or several. Use this skill whenever the user talks about float, total or free float, slack, near-critical work, float blocks, fragments or fragnets, the critical path method, or a Primavera P6 schedule or P6 XML file, or says things like "check block 7" or "what's in block 0", even if the words "float block" never come up. Schedule files are exchanged in P6 XML.
---

# CPM float blocks

This method reads a schedule by its float. Each activity's total float names the block it belongs to: "block 5" means every activity with 5 days of total float, and block 0 is the critical work. Blocks pair with fragments, the pieces of linked logic inside them. Activities usually share a float value because they are linked into one fragment, and checking that block by block shows how the schedule's slack is actually arranged.

## Terms

**Total float** is how far an activity can slip before it moves the project finish, or the must-finish date when there is one. P6 measures it by default as late finish minus early finish, in work time on the activity's own calendar.

**Free float** is how far an activity can slip before it moves the early date of any successor.

**Block** means all the activities with the same total float, named by that value. Keep every value as its own block. Don't merge neighboring values into ranges such as "2 to 5 days", because a range mixes blocks that will be discussed one at a time.

**Fragment** means a set of activities tied to one another by logic: a piece of the network, the fragnet of delay analysis. Within a block, a fragment is a group of block members connected through relationships among themselves.

**Units**: float is counted in working days of the activity's calendar. On a five-day calendar, 5 days is one week, so block 5 holds a week of slack. On a seven-day calendar, 5 days is five calendar days.

## Why blocks and fragments go together

A chain of activities with no gaps between them shares one total float, since delaying any of them uses up the same slack. The chain's free float sits on its last activity, where the chain joins work with less float. That is why a block is expected to be a single fragment.

Equal float doesn't prove a link, so check every block rather than assume it. Unrelated pieces of the network can land on the same value by coincidence, and multiple calendars, constraints and resource leveling make that more likely. Report a block that holds several fragments as exactly that.

The reverse happens too. One fragment can spread across several blocks when its activities use different calendars, because the same slack counted in five-day working days and in seven-day days gives different numbers. Look at the calendars before reading meaning into a fragment that changes block partway along. In the same way, a nonwork window in a calendar can hold an activity until the window opens. The work feeding that activity then shares the slack before the window, and the zero-float work starts at that activity instead of at the project start.

## Workflow

1. **Get the network.** The method needs the activities (ID, name, remaining duration, calendar, type), the relationships (predecessor, successor, type, lag), the calendars (work week and exceptions), the data date, and any must-finish date or constraints. Schedule files move in P6 XML. If the network arrives another way, such as a table or a list in the conversation, write it as P6 XML following `references/p6-xml.md`, so the same script reads it and it can go to P6. Ask for anything missing rather than filling it in, because a guessed duration or link moves activities between blocks.

2. **Run the CPM.** Use the bundled script rather than computing by hand; calendar arithmetic is where hand calculation goes wrong.
   ```bash
   python scripts/cpm_blocks.py schedule.xml --summary
   ```
   The script reads the project's schedule options (total float type, lag calendar, open-ended activities) and runs the forward and backward pass with FS, SS, FF and SF links, lags, milestones, constraints and calendar exceptions. If the schedule uses something the script does not model, it stops with exit status 2 and names the feature. Tell the user what it found instead of working around it, because float computed without that feature would put activities in the wrong blocks.

3. **Check against P6.** When the file carries P6-calculated dates, the script compares every activity's early and late dates and total float with them. If activities differ, list them and look for the cause before using the blocks: a file not rescheduled after edits, calendar inheritance (rerun with `--base-exceptions ignore` to test it), or leveled dates. Don't present unchecked or mismatched float as P6's.

4. **Read the blocks.** `--summary` gives one line per block with its activity and fragment counts. `--block N` lists that block's fragments with each activity's dates, free float and calendar, and what each fragment feeds. With no option the script lists every block, and `--csv out.csv` writes one row per activity.

5. **Report** in the format below. Leave out the Gantt chart unless asked, since the blocks are the deliverable.

## Report format

Open with the result of the check against P6 in one sentence. For an overview, give one line per block, from the lowest float up:

```
Block 0: 12 activities, 1 fragment
Block 3: 4 activities, 2 fragments
```

Follow with a sentence or two on what the method flags: blocks with more than one fragment, fragments spread across blocks by calendars, and where the zero-float work begins.

When the user asks about one block ("check block 5"), list its fragments, and within each fragment the activities in logic order with early start, early finish and free float. Say which activity carries the fragment's free float and what it feeds.

## Example

A five-day schedule has Excavate (5 days) then Footings (5 days); Order rebar (1 day) then Deliver rebar (2 days), which must also finish before Footings; and Utility relocation (8 days) on its own. The script gives:

```
Block 0: 2 activities, 1 fragment      Excavate → Footings
Block 2: 3 activities, 2 fragments     Order rebar → Deliver rebar (free float 2 on Deliver rebar, feeds Footings)
                                       Utility relocation (free float 2, to the project finish)
```

Block 2 is two fragments that share a value by coincidence, which is the case the fragment check exists to catch.

## What the script does not model

It stops on activities in progress, level-of-effort or WBS summary activities that carry logic, Mandatory and As Late As Possible constraints, and expected finish dates. It warns when resource leveling or resource calendars could make P6's dates differ, and when a link lands in nonwork time on a mixed-calendar path, where P6's handling should be compared. Completed activities, and level-of-effort or WBS summary activities without logic, are left out of the blocks and counted in the report header.

## Files

- `scripts/cpm_blocks.py`: the CPM engine and block report. Run it with `--help` for the options.
- `references/p6-xml.md`: the P6 XML elements and units the script reads. Read it when writing a P6 XML file or tracing a mismatch with P6.
