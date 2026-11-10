# Listening Study

Blind listening survey of the music-EBT Master's thesis (English and Italian).

Live: https://rebeccaceccatelli.github.io/listening-study/survey/ (Italian: `/survey/it/`)

The pages are not copied here: the Pages workflow checks out `demo/showcase/site/survey/` from
[music_EBT](https://github.com/RebeccaCeccatelli/music_EBT) (built by `demo/survey/`) and publishes it under
`survey/`, with `root/index.html` forwarding the bare address there. Responses go to the study's Google Sheet
through the Apps Script endpoint in `survey/config.js`.

To redeploy after a change in music_EBT: `gh workflow run pages.yml --repo RebeccaCeccatelli/listening-study`.
