import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from PIL import Image

from tools.stage_unity_reference import bottom_up_rgba, stage_reference


def digest(data):
    return hashlib.sha256(data).hexdigest()


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reference = self.root / "reference-output"
        self.reference.mkdir()
        self.project = self.root / "Unity/AncientConquest"
        sources = []
        for name in ("installed/ancient.exe", "installed/missions/controlm.dkx",
                     "installed/missions/controlm.dkd"):
            path = self.root / "reference/raw/ancient-conquest" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            sources.append({"path": str(path.relative_to(self.root)),
                            "sha256": digest(path.read_bytes())})
        image = Image.new("RGB", (800, 600), (12, 34, 56))
        image.putpixel((0, 0), (1, 2, 3))
        image.putpixel((0, 599), (4, 5, 6))
        png = self.reference / "main-menu-state0.png"
        image.save(png)
        self.manifest = {"size": [800, 600], "runtime_screenshot": False,
                         "sources": sources, "png_sha256": digest(png.read_bytes()),
                         "pixels_sha256": digest(image.tobytes())}
        (self.reference / "manifest.json").write_text(json.dumps(self.manifest))

    def test_rgba_bottom_up_keeps_channels_and_alpha(self):
        image = Image.new("RGBA", (1, 2))
        image.putdata([(1, 2, 3, 4), (5, 6, 7, 8)])
        self.assertEqual(bottom_up_rgba(image), bytes((5, 6, 7, 8, 1, 2, 3, 4)))

    def test_stages_verified_reference_and_reuses_identical_bytes(self):
        metadata = stage_reference(self.reference, self.project, repository=self.root)
        output = self.project / "Assets/Resources/LegacyReferenceGenerated/MenuRgba.bytes"
        data = output.read_bytes()
        self.assertEqual(len(data), 800 * 600 * 4)
        self.assertEqual(data[:4], bytes((4, 5, 6, 255)))
        self.assertEqual(data[-800 * 4:-800 * 4 + 4], bytes((1, 2, 3, 255)))
        self.assertEqual(metadata["payload_sha256"], digest(data))
        before = output.stat().st_mtime_ns
        self.assertEqual(stage_reference(self.reference, self.project, repository=self.root), metadata)
        self.assertEqual(output.stat().st_mtime_ns, before)

    def test_changed_original_source_or_png_refused_before_outputs(self):
        original = self.root / self.manifest["sources"][0]["path"]
        original.write_bytes(b"changed source")
        with self.assertRaisesRegex(ValueError, "source hash changed"):
            stage_reference(self.reference, self.project, repository=self.root)
        self.assertFalse(self.project.exists())
        original.write_bytes(b"installed/ancient.exe")
        png = self.reference / "main-menu-state0.png"
        png.write_bytes(png.read_bytes() + b"tampering")
        with self.assertRaisesRegex(ValueError, "PNG hash"):
            stage_reference(self.reference, self.project, repository=self.root)
        self.assertFalse(self.project.exists())

    def test_different_existing_payload_is_preserved(self):
        stage_reference(self.reference, self.project, repository=self.root)
        output = self.project / "Assets/Resources/LegacyReferenceGenerated/MenuRgba.bytes"
        output.write_bytes(b"existing user data")
        with self.assertRaises(FileExistsError):
            stage_reference(self.reference, self.project, repository=self.root)
        self.assertEqual(output.read_bytes(), b"existing user data")


class ViewportCompilationTests(unittest.TestCase):
    def test_plain_csharp_viewport_on_installed_unity_mono(self):
        editor = Path("/workspace/toolchains/Unity/6000.3.27f2/Editor")
        mono = editor / "Data/MonoBleedingEdge/bin/mono"
        compiler = editor / "Data/MonoBleedingEdge/lib/mono/4.5/csc.exe"
        if not mono.is_file() or not compiler.is_file():
            self.skipTest("Unity Mono compiler is not installed")
        source = Path(__file__).resolve().parents[1] / "Unity/AncientConquest/Assets/AncientConquest/Runtime/NativeMenuCanvas.cs"
        program = r'''using System;
using AncientConquest.Presentation;
class NativeCanvasChecks {
 static void Check(int w,int h,double x,double y,double fw,double fh) {
  var r=NativeMenuCanvas.FullScreen(w,h);
  if(Math.Abs(r.X-x)>1e-8 || Math.Abs(r.Y-y)>1e-8 ||
     Math.Abs(r.ScreenWidth-fw)>1e-8 || Math.Abs(r.ScreenHeight-fh)>1e-8)
   throw new Exception("Unexpected viewport: "+w+"x"+h);
 }
 static void Main() {
  if(NativeMenuCanvas.Width!=1920 || NativeMenuCanvas.Height!=1080)throw new Exception("Wrong native target");
  Check(1920,1080,0,0,1920,1080);
  Check(2560,1440,0,0,2560,1440);
  Check(720,1280,0,0,720,1280);
  Check(800,600,0,0,800,600);
  foreach(var p in new[]{new[]{0,600},new[]{800,0},new[]{-1,1},new[]{1,-1}}) {
   bool rejected=false;
   try{NativeMenuCanvas.FullScreen(p[0],p[1]);}catch(ArgumentOutOfRangeException){rejected=true;}
   if(!rejected)throw new Exception("Invalid viewport accepted");
  }
  Console.WriteLine("8 native full-canvas cases passed");
 }
}'''
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            test = root / "ViewportChecks.cs"
            test.write_text(program)
            output = root / "ViewportChecks.exe"
            compiled = subprocess.run([str(mono), str(compiler), "-nologo", "-target:exe",
                                       "-out:" + str(output), str(source), str(test)],
                                      capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run([str(mono), str(output)], capture_output=True,
                                    text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("8 native full-canvas cases passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
