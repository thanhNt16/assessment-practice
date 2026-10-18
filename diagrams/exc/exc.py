"""Shared Excalidraw element builder for course diagrams.

Usage:
    import sys; sys.path.insert(0, 'diagrams/exc')
    import exc
    d = exc.new_doc()
    E = exc.B()                      # builder w/ auto ids
    d['elements'] += [
        E.title(60, 40, "My Diagram"),
        E.sub(60, 72, "subtitle caption"),
        E.rect(200, 160, 300, 110, exc.BLUE_S, exc.BLUE_F,
               label="Leader\nacks gate: min.insync=2"),
        ...
    ]
    exc.save(d, 'diagrams/exc/my-diagram.excalidraw')

Coordinates: all elements position at (x, y) top-left; arrows/lines take
absolute (x, y) + points [[dx,dy], ...] ABSOLUTE offsets (each point is
added to x,y — NOT cumulative deltas).
Fonts: fontFamily 5 = Excalifont hand-drawn. Sizes: title 26,
section 17, box label 14, caption 12-13.
Style: roughness 1 (hand-drawn) everywhere.
"""

import json, random

# palette (semantic)
BLUE_S, BLUE_F   = "#1e3a5f", "#dbeafe"   # primary box / flow
BLUE2_S, BLUE2_F = "#3b82f6", "#bfdbfe"   # secondary / accent box
GREEN_S, GREEN_F = "#047857", "#a7f3d0"   # success / consumer / sink
AMBER_S, AMBER_F = "#b45309", "#fef3c7"   # warning / config
RED, ORANGE      = "#dc2626", "#c2410c"   # error text / producer stroke
GRAY, INK        = "#64748b", "#374151"   # captions / label text
HDR              = "#1e40af"              # titles + section headers
WHITE            = "#ffffff"

_seed = [1000]

class B:
    def _id(self, p):
        _seed[0] += 1
        return f"{p}-{_seed[0]}"
    def _base(self, x, y, w, h):
        return {"x": x, "y": y, "width": w, "height": h, "angle": 0,
                "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
                "opacity": 100, "fillStyle": "solid", "isDeleted": False,
                "groupIds": [], "boundElements": None, "link": None,
                "locked": False, "seed": _seed[0], "version": 1,
                "versionNonce": _seed[0]}

    def text(self, x, y, w, h, text, size=13, color=GRAY, align="left",
             container=None, bold=False):
        e = {**self._base(x, y, w, h), "id": self._id("t"), "type": "text",
             "text": text, "originalText": text, "fontSize": size,
             "fontFamily": 5, "textAlign": align, "verticalAlign": "middle",
             "strokeColor": color, "backgroundColor": "transparent",
             "strokeWidth": 1, "lineHeight": 1.25}
        if container: e["containerId"] = container
        return e

    def title(self, x, y, text, size=26):
        return self.text(x, y, len(text)*size*0.62+20, size*1.3, text, size, HDR)

    def sub(self, x, y, text, size=15):
        return self.text(x, y, len(text)*size*0.60+20, size*1.35, text, size, "#3b82f6")

    def sect(self, x, y, text, size=17):
        return self.text(x, y, len(text)*size*0.60+20, size*1.4, text, size, HDR)

    def _box(self, typ, x, y, w, h, stroke, fill, label="", dashed=False,
             lsize=14, lcolor=INK):
        e = {**self._base(x, y, w, h), "id": self._id("b"), "type": typ,
             "strokeColor": stroke, "backgroundColor": fill}
        if dashed: e["strokeStyle"] = "dashed"
        if typ == "rectangle": e["roundness"] = {"type": 3}
        if label:
            t = self.text(x+12, y+10, w-24, h-20, label, lsize, lcolor,
                          "center", e["id"])
            e["boundElements"] = [{"id": t["id"], "type": "text"}]
            return [e, t]
        return [e]

    def rect(self, x, y, w, h, stroke, fill, label="", dashed=False,
             lsize=14, lcolor=INK):
        return self._box("rectangle", x, y, w, h, stroke, fill, label,
                         dashed, lsize, lcolor)

    def ellipse(self, x, y, w, h, stroke, fill, label="", lsize=14, lcolor=INK):
        return self._box("ellipse", x, y, w, h, stroke, fill, label,
                         False, lsize, lcolor)

    def arrow(self, x, y, pts, color=BLUE_S, label=None, dashed=False,
              lsize=12, start=None, end=None):
        e = {**self._base(x, y, abs(pts[-1][0]-pts[0][0])+1,
                          abs(pts[-1][1]-pts[0][1])+1),
             "id": self._id("a"), "type": "arrow", "points": pts,
             "strokeColor": color, "backgroundColor": "transparent",
             "startArrowhead": None, "endArrowhead": "arrow"}
        if dashed: e["strokeStyle"] = "dashed"
        if start: e["startBinding"] = {"elementId": start, "focus": 0, "gap": 2}
        if end:   e["endBinding"]   = {"elementId": end,   "focus": 0, "gap": 2}
        out = [e]
        if label:
            lx = (pts[0][0]+pts[-1][0])/2 + x
            ly = (pts[0][1]+pts[-1][1])/2 + y - 22
            out.append(self.text(lx-120, ly, 240, 18, label, lsize, GRAY, "center"))
        return out

    def line(self, x, y, pts, color=GRAY, dashed=True):
        e = self.arrow(x, y, pts, color, dashed=dashed)[0]
        e["type"] = "line"; e["endArrowhead"] = None
        e.pop("startBinding", None); e.pop("endBinding", None)
        return e


def new_doc():
    return {"type": "excalidraw", "version": 2, "source": "course-diagrams",
            "elements": [], "appState": {"gridSize": None,
            "viewBackgroundColor": "#ffffff"}, "files": {}}

def save(d, path):
    # elements built via B() return lists; flatten
    flat = []
    for e in d["elements"]:
        flat.extend(e if isinstance(e, list) else [e])
    d["elements"] = flat
    json.dump(d, open(path, "w"), indent=1)
    return path
