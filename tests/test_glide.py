import unittest, sys, pathlib, importlib.util, re
spec = importlib.util.spec_from_file_location("build", pathlib.Path(__file__).parent.parent / "build.py")

def load_build():
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class GlideTest(unittest.TestCase):
    def test_parse(self):
        b = load_build()
        src = "## T\n\n:::glide My Flow\n1) A :: first\n2) B :: second\n? Q :: A\n:::\n\n### s\n"
        out, mer, glides, scenarios = b.preprocess(src)
        self.assertEqual(len(glides), 1)
        g = glides[0]
        self.assertEqual(g["title"], "My Flow")
        self.assertEqual(g["steps"], [{"n":1,"label":"A","caption":"first"},{"n":2,"label":"B","caption":"second"}])
        self.assertEqual(g["quiz"], [{"q":"Q","a":"A"}])
    def test_html_shape(self):
        b = load_build()
        h = b.glide_html({"title":"T","steps":[{"n":1,"label":"L","caption":"C"}],"quiz":[{"q":"Q","a":"A"}]})
        for needle in ['class="glide"','glide-chip','glide-cap','qflip','◀','▶','1/1']:
            self.assertIn(needle, h)
    def test_bad_line_raises(self):
        b = load_build()
        with self.assertRaises(ValueError):
            b.preprocess("## T\n\n:::glide X\n1) missing sep\n:::\n")

if __name__ == "__main__":
    unittest.main()
