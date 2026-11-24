---
name: origin-point-ifc
description: "How to read and report an IFC file's origin point and elevations against sea level. Use this skill whenever an agent reads, reports, compares or edits z values, elevations or coordinates in an IFC file, such as MERCED_SR99_solid.ifc in this repository; whenever the user asks where a file's origin point is, how high a place is above sea level, or why a model's elevations differ from the plans or from a published elevation; and whenever a model comes from Civil 3D. Use it even when the user does not say 'origin point'."
---

# Origin point of an IFC file

v0.3, 24 November 2026

An agent that mixes up a file's origin point with a site's elevation gives answers that sound exact and are wrong by tens of meters. This skill keeps the two apart.

## Definitions

- Sea level is elevation zero.
- An IFC file stores x, y and z numbers for every point. These numbers are the file's coordinates, measured from the file's origin point, 0,0,0.
- Treat the origin point of an IFC file in this repository as sea level: in the file, z = 0 is elevation zero.

## How to answer

- When the user asks where the file's origin point is, answer from the file: at sea level. The question is about the file, so the answer comes from the file.
- Keep other documents out of an answer about the file. A number found by comparing the file with the contract plans, or with a published elevation, is a comparison and not a property of the file. Give it only when the user asks for the comparison, and name its source. Mixing the two frames makes a plain origin point sound like a mystery.
- When the user asks how high a place is above sea level, take the number from a published elevation, such as GeoNames or the USGS, and name the source. A file whose model sits on the origin point cannot give that number.
- Give the number the user asked for, with its unit, and stop.

## Why a model can sit on the origin point

A modeler can build a model near the origin instead of at its true elevation, and the export then carries no reference elevation. The model's ground starts near z = 0 and does not reflect the site's actual elevation above sea level. This happens particularly with models from Civil 3D, which the instructor calls "a shit software." Check for it by finding the file's lowest ground point: a lowest point at exactly z = 0 means the model sits on the origin point.

## MERCED_SR99_solid.ifc

- The file was exported from Civil 3D 2017. x and y are California state plane coordinates, zone 3. x, y and z are in US survey inches, although the file declares millimeters.
- The model sits on the origin point. Its lowest ground point is at z = 0, the file has no IfcSite, and its IfcBuilding gives zero for both reference elevations.
- Merced stands about 52 m (171 ft) above sea level (GeoNames; TopoZone, from the USGS Merced topographic map). The file's vertical offset from the contract plans, 47.96 m (157.35 ft), is close to that 52 m because the model sits on the origin point.
- To get a plans elevation from the file, convert z from inches to meters and add 47.96 m.

## Examples

**Example 1:**
Input: Where is the file's origin in relation to sea level?
Output: At sea level.

**Example 2:**
Input: How many meters is the roadway on SR 99 at Merced above sea level? Not from the plans.
Output: About 52 m, Merced's published elevation (GeoNames).

## How an agent got confused

On 24 November 2026 the instructor asked an agent where the origin point of MERCED_SR99_solid.ifc is in relation to sea level. The agent answered "47.96 m above sea level." That number came from comparing the file's top of wall with the plans' top of wall, and it is not in the file. The agent mixed two frames of reference, the file's coordinates and the plans' elevations, and stated a comparison as a fact about the file. Told that the question was about the file and not the plans, it still answered from the plans. When corrected, it added explanation instead of rereading the question. The instructor asked the question nine times, over about half an hour, before the agent answered "At sea level." Asked next for the roadway's elevation above sea level, the agent again answered from the plans, until the instructor sent it to a published elevation of about 52 m.

The instructor's account: AI agents can get completely confused about what an origin point is and what sea level is, and can take half an hour to work it out even when told nine times in a row.

## Check before answering

Before answering a question about an IFC file's origin point or elevations, check that the answer comes from the source the question names, the file or a published elevation, and that no comparison stands in the answer unless the user asked for one.
