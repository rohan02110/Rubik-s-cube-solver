STRING_ORDER = ["U", "R", "F", "D", "L", "B"]

def build_cubestring(faces):
    centers = [faces[f][4] for f in STRING_ORDER]
    if len(set(centers)) != 6:
        raise ValueError("Two faces have the same center color — check the Verify step.")
    color_to_face = dict(zip(centers, STRING_ORDER))
    try:
        return "".join(color_to_face[c] for f in STRING_ORDER for c in faces[f])
    except KeyError as e:
        raise ValueError(f"Color '{e.args[0]}' is used on stickers but is not the center color of any face.")