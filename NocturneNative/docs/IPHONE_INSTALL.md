# Updating your existing GitHub build to v5

This document addresses the repository setup shown in your screenshots:
Satrooper/nocturne-native, with a root workflow that compiles an unsigned IPA
from a `Nocturne-Native-Project*.zip` source archive.

1. Keep a backup of your earlier ZIP and IPA.
2. Replace the old source ZIP in the repository with
   `Nocturne-Native-Project-v5.zip`. Keep exactly one source ZIP matching
   `Nocturne-Native-Project*.zip` in the repository root.
3. Keep the existing root `.github/workflows` build workflow.
4. Run that workflow from Actions. Wait for the build result, then download its
   artifact from the workflow run summary. Extract it to find the new unsigned IPA.
5. Use your Windows signing/install setup to sign that IPA and install it on your
   iPhone. An unsigned IPA cannot be installed by tapping it in Files.

The project folder within this ZIP remains `NocturneNative/` for compatibility
with the earlier archive-based workflow. Version metadata is 0.5 / build 5.
The bundle identifier remains `com.sathya.nocturne`, so a signed v5 installation
with the same app identity can replace the previous installed version. v5 uses
the existing `progress_v3.cfg` for campaign unlocks.

The nested `.github/workflows/ios-project.yml` inside the source folder is an
older alternative for preparing an Xcode project; it is not a replacement for
your currently working root IPA-build workflow.

v5 has not been built or installed on an iPhone in this session. No signing
credentials are included. Native installation remains a separate step from
source generation and desktop validation. After installation, test movement,
simultaneous touch aiming/firing, all stages, pause/resume and sustained frame rate.
