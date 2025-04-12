import json
import hashlib


def rgba_to_hex(rgba):
    """
    Convert an RGBA dict into a #RRGGBB hex string (ignoring alpha).
    """
    r = int(rgba["r"] * 255)
    g = int(rgba["g"] * 255)
    b = int(rgba["b"] * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def style_hash(style_data):
    """
    Create a hash from style data to use as a unique identifier.
    """
    style_str = json.dumps(style_data, sort_keys=True)
    return hashlib.md5(style_str.encode()).hexdigest()


def figma_align_to_flex(figma_val):
    """
    Convert Figma alignment values to CSS flex values.
    """
    align_map = {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "SPACE_BETWEEN": "space-between",
    }
    return align_map.get(figma_val, "flex-start")


def get_fill_style_id(fills, styles):
    """
    Process fill styles and add them to the styles dictionary.
    """
    if not fills or not fills[0].get("visible", True):
        return None

    fill = fills[0]

    if fill["type"] == "SOLID":
        color = fill["color"]
        opacity = fill.get("opacity", 1)

        # Create a style object
        style_data = {"backgroundColor": rgba_to_hex(color), "opacity": opacity}

        # Generate a unique ID for this style
        style_id = style_hash(style_data)

        # Add to styles dictionary if not already present
        if style_id not in styles:
            styles[style_id] = style_data

        return style_id

    return None


def get_layout_style_id(raw_node, styles):
    """
    Process layout styles and add them to the styles dictionary.
    """
    layout_style = {}

    # Extract layout properties
    if "layoutMode" in raw_node:
        layout_mode = raw_node["layoutMode"]

        if layout_mode == "HORIZONTAL":
            layout_style["display"] = "flex"
            layout_style["flexDirection"] = "row"
        elif layout_mode == "VERTICAL":
            layout_style["display"] = "flex"
            layout_style["flexDirection"] = "column"

        # Process padding
        if "paddingLeft" in raw_node:
            layout_style["paddingLeft"] = f"{raw_node['paddingLeft']}px"
        if "paddingRight" in raw_node:
            layout_style["paddingRight"] = f"{raw_node['paddingRight']}px"
        if "paddingTop" in raw_node:
            layout_style["paddingTop"] = f"{raw_node['paddingTop']}px"
        if "paddingBottom" in raw_node:
            layout_style["paddingBottom"] = f"{raw_node['paddingBottom']}px"

        # Process spacing
        if "itemSpacing" in raw_node:
            layout_style["gap"] = f"{raw_node['itemSpacing']}px"

        # Process alignment
        if "primaryAxisAlignItems" in raw_node:
            primary_align = raw_node["primaryAxisAlignItems"]
            counter_align = raw_node.get("counterAxisAlignItems", "MIN")

            def align_map_primary(val):
                if layout_mode == "HORIZONTAL":
                    return figma_align_to_flex(val)
                return figma_align_to_flex(val)

            def align_map_counter(val):
                if layout_mode == "HORIZONTAL":
                    return figma_align_to_flex(val)
                return figma_align_to_flex(val)

            layout_style["justifyContent"] = align_map_primary(primary_align)
            layout_style["alignItems"] = align_map_counter(counter_align)

    # Process size constraints
    if "absoluteBoundingBox" in raw_node:
        bbox = raw_node["absoluteBoundingBox"]
        layout_style["width"] = f"{bbox['width']}px"
        layout_style["height"] = f"{bbox['height']}px"

    # Process border radius
    border_radius = get_border_radius(raw_node)
    if border_radius:
        layout_style["borderRadius"] = border_radius

    # Process corner smoothing
    corner_smoothing = get_corner_smoothing(raw_node)
    if corner_smoothing:
        layout_style["borderRadius"] = corner_smoothing

    # Generate a unique ID for this style if it's not empty
    if layout_style:
        style_id = style_hash(layout_style)

        # Add to styles dictionary if not already present
        if style_id not in styles:
            styles[style_id] = layout_style

        return style_id

    return None


def get_border_radius(raw_node):
    """
    Extract border radius from a node.
    """
    if "cornerRadius" in raw_node:
        return f"{raw_node['cornerRadius']}px"
    return None


def get_corner_smoothing(raw_node):
    """
    Extract corner smoothing from a node.
    """
    if "cornerSmoothing" in raw_node and raw_node["cornerSmoothing"] > 0:
        return f"{raw_node['cornerSmoothing']}px"
    return None


def get_text_style_id(raw_node, styles):
    """
    Process text styles and add them to the styles dictionary.
    """
    if raw_node["type"] != "TEXT" or "style" not in raw_node:
        return None

    text_style = {}
    node_style = raw_node["style"]

    # Extract text properties
    if "fontFamily" in node_style:
        text_style["fontFamily"] = node_style["fontFamily"]
    if "fontWeight" in node_style:
        text_style["fontWeight"] = node_style["fontWeight"]
    if "fontSize" in node_style:
        text_style["fontSize"] = f"{node_style['fontSize']}px"
    if "lineHeightPx" in node_style:
        text_style["lineHeight"] = f"{node_style['lineHeightPx']}px"
    if "letterSpacing" in node_style:
        text_style["letterSpacing"] = f"{node_style['letterSpacing']}px"
    if "textAlignHorizontal" in node_style:
        align_map = {
            "LEFT": "left",
            "CENTER": "center",
            "RIGHT": "right",
            "JUSTIFIED": "justify",
        }
        text_style["textAlign"] = align_map.get(
            node_style["textAlignHorizontal"], "left"
        )

    # Process fill color for text
    if "fills" in raw_node and raw_node["fills"]:
        fill = raw_node["fills"][0]
        if fill["type"] == "SOLID":
            text_style["color"] = rgba_to_hex(fill["color"])

    # Generate a unique ID for this style if it's not empty
    if text_style:
        style_id = style_hash(text_style)

        # Add to styles dictionary if not already present
        if style_id not in styles:
            styles[style_id] = text_style

        return style_id

    return None


def transform_node(raw_node, styles):
    """
    Transform a Figma node into a simplified structure.
    """
    node_type = raw_node["type"]

    # Basic node properties
    node = {
        "id": raw_node["id"],
        "name": raw_node["name"],
        "type": node_type,
        "visible": raw_node.get("visible", True),
    }

    # Process styles
    fill_style_id = get_fill_style_id(raw_node.get("fills", []), styles)
    if fill_style_id:
        node["fillStyleId"] = fill_style_id

    layout_style_id = get_layout_style_id(raw_node, styles)
    if layout_style_id:
        node["layoutStyleId"] = layout_style_id

    text_style_id = get_text_style_id(raw_node, styles)
    if text_style_id:
        node["textStyleId"] = text_style_id

    # Process text content
    if node_type == "TEXT" and "characters" in raw_node:
        node["characters"] = raw_node["characters"]

    # Process image content
    if node_type == "RECTANGLE" and "fills" in raw_node:
        for fill in raw_node.get("fills", []):
            if fill["type"] == "IMAGE" and "imageRef" in fill:
                node["imageRef"] = fill["imageRef"]

    # Process children
    if "children" in raw_node:
        node["children"] = []
        for child in raw_node["children"]:
            # Skip invisible nodes
            if not child.get("visible", True):
                continue

            transformed_child = transform_node(child, styles)
            node["children"].append(transformed_child)

    # Process component properties
    if "componentPropertyReferences" in raw_node:
        prop_refs = raw_node["componentPropertyReferences"]
        node["componentPropertyReferences"] = prop_refs

    # Process component properties
    if "componentProperties" in raw_node:
        node["componentProperties"] = raw_node["componentProperties"]

    # Process component property definitions
    if "componentPropertyDefinitions" in raw_node:
        prop_defs = raw_node["componentPropertyDefinitions"]
        node["componentPropertyDefinitions"] = prop_defs

    # Process variants
    if "variantProperties" in raw_node:
        node["variantProperties"] = raw_node["variantProperties"]

    # Process component set
    if "componentSetId" in raw_node:
        node["componentSetId"] = raw_node["componentSetId"]

    # Process component
    if "componentId" in raw_node:
        node["componentId"] = raw_node["componentId"]

    return node


def transform_figma_json(raw_data):
    """
    Transform Figma JSON data into a simplified structure.
    """
    # Initialize styles dictionary
    styles = {}

    # Transform the document
    if isinstance(raw_data, dict) and "document" in raw_data:
        document = transform_node(raw_data["document"], styles)
    else:
        document = transform_node(raw_data, styles)

    # Return the transformed data
    return {"document": document, "styles": styles}
