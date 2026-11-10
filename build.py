"""Stage the listening survey for GitHub Pages, with its audio packed into ~1 MB chunks.

GitHub Pages deploys of the survey with its 484 separate MP3s kept stalling at "syncing_files"; the Listening
Archive, which serves its audio as ~1 MB chunks, deploys fine. So this copy does the same:

  survey/audio/<hash>.mp3 (484 files)  ->  survey/audio/pack-<n>.mp3 + survey/audio/pack.json {hash: [n, offset, length]}

and the one line of survey.js (EN and IT) that sets the player's source is swapped for a lookup that fetches the
chunk once, slices the clip out and plays it from a Blob URL. Nothing else in the survey changes; the source in
music_EBT (and the Netlify copy) keeps the plain files.

Usage (in the workflow): python3 build.py <music_EBT survey dir> <output dir>
"""
import json
import shutil
import sys
from pathlib import Path

CHUNK = 1_000_000

SHIM = r"""<script>
// GitHub copy only: clips are packed into ~1 MB chunks (see build.py in the listening-study repo).
(() => {
  const base = new URL("%s", location.href);
  let index = null;
  const chunks = {}, urls = {};
  const idx = () => index || (index = fetch(new URL("pack.json", base)).then((r) => r.json()));
  const chunk = (n) => chunks[n] || (chunks[n] = fetch(new URL(`pack-${n}.mp3`, base)).then((r) => {
    if (!r.ok) throw new Error(`audio chunk ${n}: ${r.status}`);
    return r.arrayBuffer();
  }));
  // Promise of a Blob URL for one clip (each chunk is fetched once, each clip sliced once).
  window.packedAudio = (hash) => {
    return urls[hash] || (urls[hash] = idx().then(async (ix) => {
      const [n, at, len] = ix[hash];
      const buf = await chunk(n);
      return URL.createObjectURL(new Blob([buf.slice(at, at + len)], { type: "audio/mpeg" }));
    }));
  };
})();
</script>
"""


def patch_js(path, rel):
    s = path.read_text()
    old_fn = "  function playCard(card, hash) {"
    old_src = f"      player.src = `{rel}${{hash}}.mp3`;\n      lastT = 0;\n"
    new_src = ("      const url = await window.packedAudio(hash);\n"
               "      if (!current || current.hash !== hash) return;   // another clip was clicked meanwhile\n"
               "      player.src = url;\n      lastT = 0;\n")
    assert s.count(old_fn) == 1 and s.count(old_src) == 1, f"survey.js changed, update build.py: {path}"
    path.write_text(s.replace(old_fn, "  async function playCard(card, hash) {").replace(old_src, new_src))


def patch_html(path, audio_rel):
    s = path.read_text()
    tag = '  <script src="survey.js"></script>'
    assert s.count(tag) == 1, path
    path.write_text(s.replace(tag, (SHIM % audio_rel) + tag))


def main(src, out):
    src, out = Path(src), Path(out)
    dst = out / "survey"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("audio"))
    mp3s = sorted((src / "audio").glob("*.mp3"))
    (dst / "audio").mkdir()
    index, n, cur, size = {}, 0, bytearray(), 0
    for f in mp3s:
        b = f.read_bytes()
        if cur and len(cur) + len(b) > CHUNK:
            (dst / "audio" / f"pack-{n}.mp3").write_bytes(cur)
            n, cur = n + 1, bytearray()
        index[f.stem] = [n, len(cur), len(b)]
        cur += b
    if cur:
        (dst / "audio" / f"pack-{n}.mp3").write_bytes(cur)
    (dst / "audio" / "pack.json").write_text(json.dumps(index, separators=(",", ":")))
    # every clip must come back byte-identical
    for f in mp3s:
        c, at, ln = index[f.stem]
        assert (dst / "audio" / f"pack-{c}.mp3").read_bytes()[at:at + ln] == f.read_bytes(), f
    patch_js(dst / "survey.js", "audio/")
    patch_js(dst / "it" / "survey.js", "../audio/")
    patch_html(dst / "index.html", "audio/")
    patch_html(dst / "it" / "index.html", "../audio/")
    print(f"{len(mp3s)} clips -> {n + 1} chunks; files: {sum(1 for _ in out.rglob('*') if _.is_file())}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
