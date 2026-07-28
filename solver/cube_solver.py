FACES = ["U", "R", "F", "D", "L", "B"]

def build_cubestring(faces):
    color_to_face = {faces[f][4]: f for f in STRING_ORDER}
    return "".join(color_to_face[c] for f in STRING_ORDER for c in faces[f])