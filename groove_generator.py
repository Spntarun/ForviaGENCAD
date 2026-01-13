"""
Groove/Clip Geometry Generator and Placement Module

Handles:
1. Creation of parametric groove shapes (Rectangular, Circular, U-Slot).
2. Calculation of placement frames on a surface.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Trsf, gp_Quaternion, gp_Ax1
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepLProp import BRepLProp_SLProps
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import topods

class GrooveType(Enum):
    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    SQUARE = "square"
    TRIANGLE = "triangle"

@dataclass
class GrooveParameters:
    width: float = 2.0
    depth: float = 1.0
    height: float = 10.0  # Extrusion height (formerly 'length')
    length: float = 10.0  # Kept for backward compatibility
    type: GrooveType = GrooveType.RECTANGULAR
    fillet_radius: float = 0.0  # Optional bottom fillet for U-shape

class GrooveGenerator:
    def __init__(self, params: GrooveParameters):
        self.params = params

    def create_shape(self) -> TopoDS_Shape:
        """Creates the primitive shape at the origin, centered on XY, extending -Z (inward depth)."""
        
        # Design choice: 
        # Origin (0,0,0) is the center of the groove on the surface.
        # Depth goes into -Z.
        
        if self.params.type == GrooveType.RECTANGULAR:
            # Box: Centered X (-w/2 to w/2), Centered Y (-l/2 to l/2), Depth Z (0 to -d)
            w = self.params.width
            l = self.params.length
            d = self.params.depth
            
            box = BRepPrimAPI_MakeBox(
                gp_Pnt(-w/2, -l/2, -d),
                w, l, d
            ).Shape()
            return box

        elif self.params.type == GrooveType.CIRCULAR:
            # Cylinder: Center at (0,0), Top at 0, Bottom at -d, Radius w/2
            r = self.params.width / 2.0
            d = self.params.depth
            
            cyl = BRepPrimAPI_MakeCylinder(
                gp_Ax2(gp_Pnt(0,0, -d), gp_Dir(0,0,1)), # Axis along Z
                r, 
                d
            ).Shape()
            return cyl

        elif self.params.type == GrooveType.SQUARE:
            # Square box: Equal width and length based on width parameter
            w = self.params.width
            d = self.params.depth
            
            # Use width for both X and Y dimensions
            box = BRepPrimAPI_MakeBox(
                gp_Pnt(-w/2, -w/2, -d),
                w, w, d
            ).Shape()
            return box

        elif self.params.type == GrooveType.TRIANGLE:
            # Triangular prism: Equilateral triangle base, extruded along Y-axis
            # Triangle centered at origin, pointing up in X-Z plane, extruded in Y
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
            from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
            
            w = self.params.width
            l = self.params.length
            d = self.params.depth
            
            # Create equilateral triangle in X-Z plane at Z=-d
            # Triangle vertices: centered at X=0, base parallel to X-axis
            h = (w * math.sqrt(3)) / 2.0  # Height of equilateral triangle
            
            # Three vertices of triangle
            p1 = gp_Pnt(-w/2, 0, -d)      # Bottom left
            p2 = gp_Pnt(w/2, 0, -d)       # Bottom right
            p3 = gp_Pnt(0, 0, -d + h)     # Top (pointing inward, toward surface)
            
            # Create edges
            edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            edge3 = BRepBuilderAPI_MakeEdge(p3, p1).Edge()
            
            # Create wire from edges
            wire_maker = BRepBuilderAPI_MakeWire()
            wire_maker.Add(edge1)
            wire_maker.Add(edge2)
            wire_maker.Add(edge3)
            wire = wire_maker.Wire()
            
            # Create face from wire
            face = BRepBuilderAPI_MakeFace(wire).Face()
            
            # Extrude along Y-axis
            prism = BRepPrimAPI_MakePrism(
                face,
                gp_Vec(0, l, 0)
            ).Shape()
            
            # Translate to center along Y
            from OCC.Core.gp import gp_Trsf
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
            trsf = gp_Trsf()
            trsf.SetTranslation(gp_Vec(0, -l/2, 0))
            prism = BRepBuilderAPI_Transform(prism, trsf).Shape()
            
            return prism

        else:
            raise NotImplementedError(f"Groove Type {self.params.type} not implemented.")

    def place_shape(self, shape: TopoDS_Shape, location: gp_Pnt, normal: gp_Dir, tangent: Optional[gp_Dir] = None) -> TopoDS_Shape:
        """
        Transforms the base shape (defined at origin, Z-down depth) to the target location.
        Aligned such that local Z axes matches the INWARD normal (or OUTWARD, depending on context).
        
        Context: The shape is created in -Z. So if we align Local Z with Surface Normal, 
        the shape will protrude INTO the surface (opposite to Normal) if the Normal points OUT.
        
        Wait, standard normal points OUT.
        Groove Depth is -Z.
        If we align Z to Normal, the groove shape (0 to -d) will go INTO the material. Correct.
        """
        
        # 1. Rotation
        # Align Local Z (0,0,1) with Surface Normal
        trsf_rot = gp_Trsf()
        q = gp_Quaternion(gp_Vec(0,0,1), gp_Vec(normal.XYZ()))
        trsf_rot.SetRotation(q)
        
        # TODO: Handle Tangent alignment (Rotation around Z) if groove has orientation (like box)
        if tangent and self.params.type != GrooveType.CIRCULAR:
             # This requires constructing a full Ax3 system
             pass

        # 2. Translation
        trsf_mov = gp_Trsf()
        trsf_mov.SetTranslation(gp_Vec(location.XYZ()))
        
        full_trsf = trsf_mov.Multiplied(trsf_rot)
        
        transformer = BRepBuilderAPI_Transform(shape, full_trsf)
        return transformer.Shape()

def compute_placement_frames(face: TopoDS_Shape, num_points: int = 5, offset_from_edge: float = 5.0) -> List[Tuple[gp_Pnt, gp_Dir]]:
    """
    Computes a list of (Point, Normal) frames along a path on the face.
    For MVP: Just samples points along the U-iso curve at the center of V (or similar heuristic).
    """
    surface = BRep_Tool.Surface(face)
    props = BRepLProp_SLProps(BRepAdaptor_Surface(face), 2, 1e-6)
    
    # Get bounds
    u_min, u_max, v_min, v_max = 0, 0, 0, 0
    # Note: BRepAdaptor_Surface gives correct bounds for the face
    adaptor = BRepAdaptor_Surface(face)
    u_min, u_max, v_min, v_max = adaptor.FirstUParameter(), adaptor.LastUParameter(), adaptor.FirstVParameter(), adaptor.LastVParameter()
    
    frames = []
    
    # Simple linear interpolation on U, fixed V mid
    v_mid = (v_min + v_max) / 2.0
    
    # If offset_from_edge is needed, we might adjust v_mid
    # But for generic placement, let's just use mid-line
    
    step_u = (u_max - u_min) / (num_points + 1)
    
    for i in range(1, num_points + 1):
        u = u_min + i * step_u
        pnt = adaptor.Value(u, v_mid)
        
        props.SetParameters(u, v_mid)
        if props.IsNormalDefined():
            normal = props.Normal()
            frames.append((pnt, normal))
            
    return frames
