---
name: cadwork-viewer-layer-lights
description: "Why the IFC Layer lights (the lamps) in the cadwork BIM Viewer do not turn elements off, and what to do about it. Use this skill whenever the user says the layer lights, the lamps or the IFC Layer panel of the cadwork BIM Viewer do not hide elements, says they cannot turn off elements one at a time, or calls an IFC file broken or corrupted because of it; before changing an IFC file's buildings, storeys or layers to fix what the viewer shows; and when choosing the IFC version of a file that students will open in the cadwork BIM Viewer. Use it even when the user does not name the viewer."
---

# Layer lights in the cadwork BIM Viewer

v0.2, 24 November 2026

On 24 November 2026 an agent spent most of an evening on the IFC Layer lights of the cadwork BIM Viewer. It moved elements into buildings and storeys and rewrote the layers, and none of it helped. One test then showed that the lights depend on the IFC version of the file. This skill keeps the next agent from repeating that.

## What the tests showed

The cadwork BIM Viewer's IFC Layer lights turn elements off in an IFC2X3 file. They do not turn elements off in an IFC4 or IFC4X3 file: the lamp turns green, and the viewer still draws the elements. cadwork's manual defines a green lamp as "All elements in this layer have been hidden (but the layer is still visible)", so in these files the viewer marks the elements hidden and keeps drawing them.

The instructor tested these files in the viewer on 24 November 2026:

| File | Schema | Written by | Layer entity | Geometry | Elements in | Lights |
|---|---|---|---|---|---|---|
| `MERCED_SR99_ifc43_mapped.ifc` and the C3D files made from it | IFC4X3_ADD2 | IfcOpenShell | IfcPresentationLayerWithStyle | Brep, SurfaceModel | site, IfcRoad, IfcBridge | Fail |
| `lights_test_site.ifc` | IFC4X3_ADD2 | IfcOpenShell | IfcPresentationLayerWithStyle | Brep | site | Fail |
| `lights_test_storey.ifc` | IFC4X3_ADD2 | IfcOpenShell | IfcPresentationLayerWithStyle | Brep | building storey | Fail |
| `lights_test_plain_layers.ifc`, here `assets/lights_test_ifc4x3.ifc` | IFC4X3_ADD2 | IfcOpenShell | IfcPresentationLayerAssignment | Brep | site | Fail |
| `lights_test_lexocad_ifc4.ifc` | IFC4 | Lexocad | IfcPresentationLayerAssignment | Tessellation | site | Fail |
| `merced_ifc43_preliminary.ifc` | IFC4X3_ADD2 | Lexocad 31's IFC 4 export, then IfcOpenShell | not read | not read | buildings and storeys | Fail |
| `lights_test_lexocad_ifc2x3.ifc`, here `assets/lights_test_ifc2x3.ifc` | IFC2X3 | Lexocad | IfcPresentationLayerAssignment | Brep | site | Work |

The five test files hold the same four elements, three curbs and an approach slab, each on its own layer. In Lexocad itself, which the viewer is built on, switching an IFC layer off hides its elements in the IFC4X3 test files too. So the files carry their layers correctly, and the viewer does not act on them.

## What the tests rule out

- The spatial structure. Elements in the site, an IfcRoad, an IfcBridge or a building storey all fail in IFC4X3, so moving elements into buildings or storeys does not fix the lights.
- The layer entity. IfcPresentationLayerWithStyle and a plain IfcPresentationLayerAssignment both fail in IFC4X3.
- The geometry. Brep and Tessellation both fail outside IFC2X3.
- The writer. A file written by Lexocad fails in IFC4 too.
- A corrupt file. The IFC4X3 files pass ifcopenshell.validate with 0 errors.

## What to do

1. When the user reports that the layer lights do not work, read the file's `FILE_SCHEMA` line first. If it says IFC4 or IFC4X3, tell the user that the viewer's layer lights do not hide elements in that schema, and point to the table above.
2. Leave the IFC 4.3 file as it is. The file is correct, and the repository's files are IFC 4.3 on purpose, so do not convert a file to IFC2X3 or IFC4 to make the lights work.
3. The fix is in the viewer, which belongs to cadwork informatik. A report to cadwork needs the two files in `assets/` and the table above.

## How to test a viewer again

Open `assets/lights_test_ifc2x3.ifc` and `assets/lights_test_ifc4x3.ifc` in the cadwork BIM Viewer, turn off one layer light in each, and see whether its element disappears. Ask the user for this test after reading the schema and before changing any file. A new viewer version may behave differently, and this test shows it in a minute.

## The lamp colours

cadwork's manual for Lexocad, section 4.1.15, gives the colours of a lamp: yellow, all elements in the layer are visible; red, at least one element has been hidden; green, all elements have been hidden, but the layer is still visible; empty, the layer and all its elements are hidden ([cadwork KB](https://kb.cadwork.ch/en/lexocad/manual/1034)).

## Limits of the tests

- One viewer: the cadwork BIM Viewer installed on the instructor's computer on 24 November 2026.
- One IFC2X3 file that works, written by Lexocad. An IFC2X3 file written by another program was not tested.

## How an agent got confused

An earlier chat saw that the viewer's Hide Site Geometry box turned everything off, and inferred that the layer lights skip elements outside a building storey. The next agent took that inference over as fact. It built a storey test, rewrote the layers in the way Lexocad writes them, and changed the geometry, one test at a time. The instructor said several times that the problem was the IFC layer lights, not the storey. A test of the same four elements exported by Lexocad in IFC4 and in IFC2X3 settled it in one step.

## Check before answering

Before changing an IFC file to fix the viewer's layer lights, check the file's `FILE_SCHEMA`, and check that the change is not one this skill rules out.
