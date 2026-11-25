# Hawk models

Hawk models for the MER99 corridor model, as IFC 4.3 files (schema IFC4X3_ADD2, metres). Each hawk is an `IfcGeographicElement` with `PredefinedType` USERDEFINED and `ObjectType` HAWK, in an `IfcSite`. Each hawk sits at its file's origin point; it is not placed at a site location.

## Carls_hawks_ifc43.ifc

- Source: MER99 saved March 25, 2011.
- Origin: the original source and license of the bird's geometry are not known. The file `eagle_36100037_block.dwg` is named after `eagle_36100037.dwg`, a drawing of 2007.
- Size: 2.32 m wing to wing. The block inserts at scale 304.8, the number of millimetres in a foot, so the block's units are read as feet. A Swainson's hawk spans 117 to 137 cm ([Smithsonian's National Zoo](https://nationalzoo.si.edu/migratory-birds/species-profile-swainsons-hawk)).
- Change: the block's 29 polyface meshes were converted to IFC 4.3, as 29 `IfcTriangulatedFaceSet` items with 17,311 triangles and one brown surface colour.
