_HEX_TO_NAME = {
    "000000": "black",
    "c0c0c0": "silver",
    "808080": "gray",
    "ffffff": "white",
    "800000": "maroon",
    "ff0000": "red",
    "800080": "purple",
    "ff00ff": "fuchsia",
    "008000": "green",
    "00ff00": "lime",
    "808000": "olive",
    "ffff00": "yellow",
    "000080": "navy",
    "0000ff": "blue",
    "008080": "teal",
    "00ffff": "aqua",
    "f0f8ff": "aliceblue",
    "faebd7": "antiquewhite",
    "7fffd4": "aquamarine",
    "f0ffff": "azure",
    "f5f5dc": "beige",
    "ffe4c4": "bisque",
    "ffebcd": "blanchedalmond",
    "8a2be2": "blueviolet",
    "a52a2a": "brown",
    "deb887": "burlywood",
    "5f9ea0": "cadetblue",
    "7fff00": "chartreuse",
    "d2691e": "chocolate",
    "ff7f50": "coral",
    "6495ed": "cornflowerblue",
    "fff8dc": "cornsilk",
    "dc143c": "crimson",
    "00ffff": "cyan",
    "00008b": "darkblue",
    "008b8b": "darkcyan",
    "b8860b": "darkgoldenrod",
    "a9a9a9": "darkgray",
    "006400": "darkgreen",
    "a9a9a9": "darkgrey",
    "bdb76b": "darkkhaki",
    "8b008b": "darkmagenta",
    "556b2f": "darkolivegreen",
    "ff8c00": "darkorange",
    "9932cc": "darkorchid",
    "8b0000": "darkred",
    "e9967a": "darksalmon",
    "8fbc8f": "darkseagreen",
    "483d8b": "darkslateblue",
    "2f4f4f": "darkslategray",
    "2f4f4f": "darkslategrey",
    "00ced1": "darkturquoise",
    "9400d3": "darkviolet",
    "ff1493": "deeppink",
    "00bfff": "deepskyblue",
    "696969": "dimgray",
    "696969": "dimgrey",
    "1e90ff": "dodgerblue",
    "b22222": "firebrick",
    "fffaf0": "floralwhite",
    "228b22": "forestgreen",
    "dcdcdc": "gainsboro",
    "f8f8ff": "ghostwhite",
    "ffd700": "gold",
    "daa520": "goldenrod",
    "adff2f": "greenyellow",
    "808080": "grey",
    "f0fff0": "honeydew",
    "ff69b4": "hotpink",
    "cd5c5c": "indianred",
    "4b0082": "indigo",
    "fffff0": "ivory",
    "f0e68c": "khaki",
    "e6e6fa": "lavender",
    "fff0f5": "lavenderblush",
    "7cfc00": "lawngreen",
    "fffacd": "lemonchiffon",
    "add8e6": "lightblue",
    "f08080": "lightcoral",
    "e0ffff": "lightcyan",
    "fafad2": "lightgoldenrodyellow",
    "d3d3d3": "lightgray",
    "90ee90": "lightgreen",
    "d3d3d3": "lightgrey",
    "ffb6c1": "lightpink",
    "ffa07a": "lightsalmon",
    "20b2aa": "lightseagreen",
    "87cefa": "lightskyblue",
    "778899": "lightslategray",
    "778899": "lightslategrey",
    "b0c4de": "lightsteelblue",
    "ffffe0": "lightyellow",
    "32cd32": "limegreen",
    "faf0e6": "linen",
    "ff00ff": "magenta",
    "66cdaa": "mediumaquamarine",
    "0000cd": "mediumblue",
    "ba55d3": "mediumorchid",
    "9370db": "mediumpurple",
    "3cb371": "mediumseagreen",
    "7b68ee": "mediumslateblue",
    "00fa9a": "mediumspringgreen",
    "48d1cc": "mediumturquoise",
    "c71585": "mediumvioletred",
    "191970": "midnightblue",
    "f5fffa": "mintcream",
    "ffe4e1": "mistyrose",
    "ffe4b5": "moccasin",
    "ffdead": "navajowhite",
    "fdf5e6": "oldlace",
    "6b8e23": "olivedrab",
    "ffa500": "orange",
    "ff4500": "orangered",
    "da70d6": "orchid",
    "eee8aa": "palegoldenrod",
    "98fb98": "palegreen",
    "afeeee": "paleturquoise",
    "db7093": "palevioletred",
    "ffefd5": "papayawhip",
    "ffdab9": "peachpuff",
    "cd853f": "peru",
    "ffc0cb": "pink",
    "dda0dd": "plum",
    "b0e0e6": "powderblue",
    "663399": "rebeccapurple",
    "bc8f8f": "rosybrown",
    "4169e1": "royalblue",
    "8b4513": "saddlebrown",
    "fa8072": "salmon",
    "f4a460": "sandybrown",
    "2e8b57": "seagreen",
    "fff5ee": "seashell",
    "a0522d": "sienna",
    "87ceeb": "skyblue",
    "6a5acd": "slateblue",
    "708090": "slategray",
    "708090": "slategrey",
    "fffafa": "snow",
    "00ff7f": "springgreen",
    "4682b4": "steelblue",
    "d2b48c": "tan",
    "d8bfd8": "thistle",
    "ff6347": "tomato",
    "40e0d0": "turquoise",
    "ee82ee": "violet",
    "f5deb3": "wheat",
    "f5f5f5": "whitesmoke",
    "9acd32": "yellowgreen",
}


def _reversedict(dict_to_reverse: dict) -> dict:
    return {value: key for key, value in dict_to_reverse.items()}


def hex_to_name(hex_color: str) -> str:
    """
    Convert a hex color code to its corresponding name.
    """
    # Remove the '#' character if present
    hex_color = hex_color.lstrip("#")
    # Check if the hex color is valid
    if len(hex_color) != 6 and len(hex_color) != 8:
        raise ValueError("Invalid hex color code. It should be a 6/8-digit hex code.")
    hex_color = hex_color[0:6]
    try:
        return _HEX_TO_NAME[hex_color.lower()]
    except KeyError:
        raise ValueError(f"Color {hex_color} not found in the color dictionary.")


def name_to_hex(color_name: str) -> str:
    """
    Convert a color name to its corresponding hex color code.
    """
    # Reverse the dictionary for easy lookup
    reversed_dict = _reversedict(_HEX_TO_NAME)
    try:
        return reversed_dict[color_name]
    except KeyError:
        raise ValueError(f"Color {color_name} not found in the color dictionary.")


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hex color code to its corresponding RGB tuple.
    """
    # Remove the '#' character if present
    hex_color = hex_color.lstrip("#")
    # Check if the hex color is valid
    if len(hex_color) != 6 and len(hex_color) != 8:
        raise ValueError("Invalid hex color code. It should be a 6/8-digit hex code.")
    # Convert the hex color to RGB
    return f"rgb({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)})"


def rgb_to_hex(rgb: str) -> str:
    """
    Convert an RGB tuple to its corresponding hex color code.
    """
    # Extract the RGBA values from the string
    try:
        rgba_values = [int(value) for value in rgb[4:-1].split(",")]
    except ValueError:
        raise ValueError(
            "Invalid RGB(A) color code. It should be in the format 'rgb(r, g, b)' or 'rgba(r, g, b, a)'."
        )
    # Check if the RGBA values are valid
    if len(rgba_values) not in (3, 4) or any(
        value < 0 or value > 255 for value in rgba_values[:3]
    ):
        raise ValueError(
            "Invalid RGB(A) color code. It should be in the format 'rgb(r, g, b)' or 'rgba(r, g, b, a)'."
        )
    # Convert the RGB values to hex
    hex_color = "#{:02x}{:02x}{:02x}".format(*rgba_values[:3])
    return hex_color


def rgb_to_name(rgb: str) -> str:
    """
    Convert an RGB tuple to its corresponding color name.
    """
    # Convert the RGB tuple to hex
    hex_color = rgb_to_hex(rgb)
    # Convert the hex color to name
    return hex_to_name(hex_color)
