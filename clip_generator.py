"""
Clip Geometry Generator Module

Handles:
1. Derivation of clip geometry from groove parameters
2. Automatic dimension calculation with assembly clearance
3. Clip shape creation with identical profile to grooves
"""

import math
from dataclasses import dataclass
from typing import Optional

from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Trsf
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

from groove_generator import GrooveParameters, GrooveGenerator, GrooveType


@dataclass
class ClipParameters:
    """Parameters for clip generation derived from groove geometry"""
    groove_params: GrooveParameters  # Reference groove geometry
    height: float  # User-specified clip height
    assembly_clearance: float = 0.2  # Width reduction for fit (mm)
    retention_offset: float = 0.1  # Depth reduction for retention (mm)
    
    def validate(self) -> tuple[bool, str]:
        """Validate clip parameters"""
        if self.height <= 0:
            return False, "Clip height must be positive"
        
        if self.assembly_clearance >= self.groove_params.width:
            return False, f"Assembly clearance ({self.assembly_clearance}mm) must be less than groove width ({self.groove_params.width}mm)"
        
        if self.retention_offset >= self.groove_params.depth:
            return False, f"Retention offset ({self.retention_offset}mm) must be less than groove depth ({self.groove_params.depth}mm)"
        
        clip_width = self.groove_params.width - self.assembly_clearance
        clip_depth = self.groove_params.depth - self.retention_offset
        
        if clip_width <= 0:
            return False, f"Calculated clip width ({clip_width}mm) must be positive"
        
        if clip_depth <= 0:
            return False, f"Calculated clip depth ({clip_depth}mm) must be positive"
        
        return True, "Valid"


class ClipGenerator:
    """
    Generates clip geometry derived from groove parameters.
    Clips have IDENTICAL shape to grooves, only scaled/offset for assembly clearance.
    """
    
    def __init__(self, params: ClipParameters):
        self.params = params
        self._derived_groove_params = None
    
    def derive_from_groove(self) -> GrooveParameters:
        """
        Creates derived groove parameters for clip generation.
        Adjusts dimensions while preserving exact geometric profile.
        """
        if self._derived_groove_params is not None:
            return self._derived_groove_params
        
        # Calculate adjusted dimensions
        clip_width = self.params.groove_params.width - self.params.assembly_clearance
        clip_depth = self.params.groove_params.depth - self.params.retention_offset
        
        # Create new groove parameters with adjusted dimensions
        # CRITICAL: Same shape type, just scaled dimensions
        self._derived_groove_params = GrooveParameters(
            width=clip_width,
            depth=clip_depth,
            height=self.params.height,  # Use clip-specific height
            length=self.params.height,  # For backward compatibility
            type=self.params.groove_params.type,  # IDENTICAL SHAPE
            fillet_radius=self.params.groove_params.fillet_radius * (clip_width / self.params.groove_params.width) if self.params.groove_params.fillet_radius > 0 else 0
        )
        
        return self._derived_groove_params
    
    def create_shape(self) -> TopoDS_Shape:
        """
        Creates clip geometry using derived groove parameters.
        The shape is IDENTICAL to the groove, just with adjusted dimensions.
        TRANSFORMED to anchor to the bottom of the groove (recessed from surface).
        """
        # Derive parameters from groove
        derived_params = self.derive_from_groove()
        
        # Use GrooveGenerator to create the shape
        # This ensures IDENTICAL geometry, just scaled
        groove_gen = GrooveGenerator(derived_params)
        shape = groove_gen.create_shape()
        
        # Anchor Clip to Groove Bottom
        # Current shape is [0 to -clip_depth] along Z
        # We want it to be [-offset to -groove_depth] along Z
        # This ensures it touches the floor of the groove and is recessed from surface
        # Shift = -retention_offset
        if self.params.retention_offset != 0:
            trsf = gp_Trsf()
            # Shift along Z-axis (which points OUT of surface in local coords, 
            # but usually Groove is -Z. Wait. GrooveGenerator makes -Z shape.
            # Local Frame Z is Normal. 
            # So shift -offset moves it deeper (into material).
            trsf.SetTranslation(gp_Vec(0, 0, -self.params.retention_offset))
            shape = BRepBuilderAPI_Transform(shape, trsf).Shape()
            
        return shape
    
    def place_shape(self, shape: TopoDS_Shape, location: gp_Pnt, normal: gp_Dir, tangent: Optional[gp_Dir] = None) -> TopoDS_Shape:
        """
        Places clip shape at target location.
        Reuses placement logic from GrooveGenerator for consistency.
        """
        derived_params = self.derive_from_groove()
        groove_gen = GrooveGenerator(derived_params)
        return groove_gen.place_shape(shape, location, normal, tangent)
    
    def get_dimensions_summary(self) -> dict:
        """Returns a summary of clip dimensions for logging/validation"""
        derived = self.derive_from_groove()
        return {
            "shape_type": derived.type.value,
            "width": derived.width,
            "depth": derived.depth,
            "height": self.params.height,
            "groove_width": self.params.groove_params.width,
            "groove_depth": self.params.groove_params.depth,
            "assembly_clearance": self.params.assembly_clearance,
            "retention_offset": self.params.retention_offset
        }
