# Tasks: Load the floor plan image on the Maps page

**Issue**: #3236 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the route tests in `tests/unit/web_portal/test_map_image_route.py`.
  Run them red.
- [x] T002 Add the browser journeys in `tests/e2e/test_map_viewer_image.py`. Run
  them red, and read each screenshot.

## Phase 2: The change

- [x] T003 Add the classes `MapImageSource` and `MapImageDownloader` to
  `web_portal/routes/maps.py`, and replace the image route.
- [x] T004 Change the map data answer and the map list to use `MapImageSource`.
- [x] T005 Add the note to `web_portal/templates/map_viewer.html`. Read the
  image result when the Plotly promise ends, and ignore a late answer.
- [x] T006 Remove the #3236 exemption from `tests/unit/web_portal/test_portal_sdk_calls.py`.
- [x] T007 Run the route tests and the browser journeys green.

## Phase 3: Finish

- [x] T008 Run a local portal with the live cloud, and read the screenshot of a
  real floor plan.
- [x] T009 Run every gate, and update `specs/005-web-portal/contracts/rest-api.md`.
- [x] T010 Add the fragment `changelog.d/issue-3236-maps-image-url.md`.
