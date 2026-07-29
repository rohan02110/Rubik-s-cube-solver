STRING_ORDER = ["U", "R", "F", "D", "L", "B"]

def build_cubestring(faces):
    centers = [faces[f][4] for f in STRING_ORDER]
    if len(set(centers)) != 6:
        raise ValueError("two faces have the same center color — check the Verify step")
    color_to_face = dict(zip(centers, STRING_ORDER))
    return "".join(color_to_face[c] for f in STRING_ORDER for c in faces[f])