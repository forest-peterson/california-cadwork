---
name: origin-point-ifc
description: "Use whenever an agent reads, reports or edits coordinates or elevations in an IFC file in this repository, such as MERCED_SR99_solid.ifc, and whenever the user asks where a file's origin point is or where it is in relation to sea level. It defines the origin point of the file, 0,0,0, as sea level, says that a question about the file is answered from the file, and records how an agent confused the file's origin with a number taken from the contract plans."
---

# Origin point of an IFC file

v0.2, 24 November 2026

## Definitions

- Sea level is elevation zero.
- An IFC file stores x, y and z numbers for every point. These numbers are the file's coordinates, measured from the file's origin point, 0,0,0.
- The origin point of an IFC file in this repository, 0,0,0, is at sea level. In the file, z = 0 is elevation zero.

## Rules

- Asked where the file's origin point is, answer from the file: at sea level.
- Answer a question about the file from the file. Do not bring in another document, such as the contract plans.
- A number found by comparing the file with another document is a comparison, not a property of the file. Give it only when the user asks for the comparison, and name the document it came from.

## MERCED_SR99_solid.ifc

- The origin point is at sea level. x and y are California state plane coordinates, zone 3. x, y and z are in US survey inches, although the file declares millimeters.
- The lowest ground point in the file is at z = 0, so the file puts the lowest ground at sea level.
- Compared with the contract plans, Contract_Plans_Merced_Rte_99.pdf, the file's elevations are 47.96 m (157.35 ft) lower than the plans' elevations. To get a plans elevation from the file, convert z from inches to meters and add 47.96 m.
- The file records no other reference elevation: it has no IfcSite, and its IfcBuilding gives zero for both reference elevations.

## When a model sits on the origin point

- Sometimes a model sits on the origin point: its ground starts at z = 0 and does not reflect the site's actual elevation above sea level. This happens particularly with models from Civil 3D, which the instructor calls "a shit software."
- MERCED_SR99_solid.ifc is such a model, exported from Civil 3D 2017. Its lowest ground point is at z = 0, but Merced stands about 52 m (171 ft) above sea level (GeoNames; TopoZone, from the USGS Merced topographic map). The file's vertical offset, 47.96 m by comparison with the contract plans, is close to that 52 m because the model sits on the origin point.

## How an agent got confused

On 24 November 2026 the instructor asked an agent where the origin point of MERCED_SR99_solid.ifc is in relation to sea level. The agent answered "47.96 m above sea level." That number came from comparing the file's top of wall with the plans' top of wall. It is not in the file.

The agent mixed two frames of reference, the file's coordinates and the plans' elevations, and stated a comparison with the plans as a fact about the file. Told that the question was about the file and not the plans, it still answered from the plans. When corrected, it added explanation instead of rereading the question. The instructor asked the question nine times, over about half an hour, before the agent answered "At sea level."

The instructor's account: AI agents can get completely confused about what an origin point is and what sea level is, and can take half an hour to work it out even when told nine times in a row.

## Check before answering

Before answering a question about an IFC file's coordinates or elevations, check that the answer comes from the file itself, and that no number from another document stands in the answer unless the user asked for the comparison.
