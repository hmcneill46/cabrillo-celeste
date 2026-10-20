# Getting Celeste game files for Cabrillo

These instructions apply to **build53 / 0.25.0 development and later**. The
published 0.24.1 / build52 has the earlier, narrower importer. Use a clean
**Celeste 1.4.0.0 FNA** download from the store where you own the game. You only
need one package; its desktop operating system need not match your computer or
iPhone/iPad.

Cabrillo imports a **ZIP**, including the game code and the entire `Content`
folder. It prepares Everest locally on the first launch, then reuses the verified
result. No game code or assets come in Cabrillo's IPA.

## Which package?

| Store | Packages covered by build53 |
| --- | --- |
| itch.io | Original Windows OpenGL/FNA, Linux and macOS 1.4.0.0 ZIPs |
| Steam | Linux 2021 and public-2025 depots, macOS FNA, Windows OpenGL/FNA |
| Epic Games Store | Original Windows and macOS FNA 1.4.0.0 packages |

These are the nine supplied distributions, identified by their actual code and
content hashes. A store label or renamed ZIP is not enough. Other game versions,
XNA, modified/Everest installations, Microsoft Store/Xbox App and console copies
are outside this verified set. A matching package from another storefront may
work, but has not been independently tested.

The [build53 report](ios-jit/GAME_INPUTS_BUILD_53.md) distinguishes import, host
gameplay and physical-device evidence. Morro's device results are separate.

## itch.io

1. Sign into the itch.io account that owns Celeste and open its library/downloads.
2. Choose the original 1.4.0.0 FNA package: Windows **OpenGL**, Linux or macOS.
3. Copy the downloaded ZIP to Files on your phone/iPad. There is no need to
   extract or rename an original ZIP.
4. In Cabrillo, choose **Play → Import game ZIP…** (or **Choose game ZIP…**).

## Steam — recommended Linux depot

Use Steam on a computer signed into an account that owns Celeste. Linux files
work as Cabrillo's input on any supported phone/tablet; you do not need to run
Linux or launch the desktop game.

1. Enter `steam://open/console` in your computer's browser and allow it to open
   Steam.
2. In Steam's **Console** tab, enter:

   ```text
   download_depot 504230 504233 5880027853585448535
   ```

3. Wait until Steam prints **Depot download complete**. Its progress display may
   stay quiet for some time. Use the exact folder path in the completion message,
   normally ending in `steamapps/content/app_504230/depot_504233`.
4. Copy that completed folder somewhere convenient, then compress the **whole
   folder** into a ZIP. Keep `Celeste.exe`, `FNA.dll`, `Steamworks.NET.dll`,
   `Celeste.Content.dll` and `Content/` together.
5. Transfer that ZIP to Files and import it in Cabrillo.

Other covered depots:

| Edition | Steam console command |
| --- | --- |
| Linux 2021 | `download_depot 504230 504233 1505052356460012099` |
| macOS FNA | `download_depot 504230 504232 3271492884622616896` |
| Windows OpenGL/FNA | `download_depot 504230 504231 1981411158533599226` |

The Windows FNA package belongs to Steam's `opengl` branch; the usual Windows
installation may be XNA. The Linux depot above is the simplest recommended route.
If Steam cannot retrieve an older manifest, use that recommended depot instead
of combining files from different installations.

Cabrillo adapts desktop Steam startup, callbacks, achievements and statistics
for local play. Steam achievements and Steam Cloud do not run inside Cabrillo.
Local game progress and Cabrillo's manual save transfers still work.

## Epic Games Store

Use a clean Windows or macOS FNA installation downloaded through your own Epic
account. Compress its complete game folder as described below. The covered Epic
Windows package legitimately omits `Celeste.Content.dll`; leave it that way.
Cabrillo creates the empty companion metadata it needs locally.

### Optional: download with Legendary

[Legendary](https://github.com/legendary-gl/legendary) is an optional open-source
Epic downloader. On a Mac with 64-bit Python 3.10 or later, an isolated Python
environment avoids changing system packages:

```sh
python3 --version
python3 -m venv "$HOME/Celeste-Download-Tools"
source "$HOME/Celeste-Download-Tools/bin/activate"
python3 -m pip install legendary-gl
legendary auth
legendary list
```

Complete Epic's sign-in in your browser. Find Celeste's **App Name** in the list;
use the value shown for your account rather than guessing it. Set it below,
replacing the placeholder, then download one platform:

```sh
CELESTE_EPIC_APP="<App Name shown by legendary list>"
mkdir -p "$HOME/Celeste-Clean-Builds/Epic"
legendary install "$CELESTE_EPIC_APP" \
  --platform Mac \
  --base-path "$HOME/Celeste-Clean-Builds/Epic" \
  --game-folder "Celeste-macOS-FNA-1.4.0.0" \
  --download-only
```

For Windows files, change `--platform Mac` to `--platform Windows` and choose a
different folder, such as `Celeste-Windows-FNA-1.4.0.0`. Wait for the download to
finish, then ZIP the complete downloaded folder. Naming the folder `1.4.0.0`
does not force Epic to serve that version: Cabrillo checks the actual files.

Legendary and the Epic account are only needed for the download. Cabrillo never
asks for their credentials. See Legendary's [installation and command
reference](https://github.com/legendary-gl/legendary#quickstart) for its supported
systems and authentication troubleshooting.

## Make the ZIP and import it

- **macOS:** in Finder, right-click the complete game folder or `Celeste.app`
  and choose **Compress**. A macOS app's files are inside
  `Celeste.app/Contents/Resources/`; you can keep the app wrapper intact.
- **Windows:** right-click the complete game folder and choose **Compress to
  ZIP file** / **Send to → Compressed (zipped) folder**, depending on Windows.
- **Linux:** use your archive manager to create a ZIP of the complete game folder.

Include one game installation in each ZIP. Cabrillo discovers the `Content/`
root inside a single wrapper or macOS app, verifies its 1,216 assets and the
matching original code, and ignores desktop native libraries. Do not ZIP just
`Content/`, just the executable, multiple platform downloads together, or a
folder that has already been modified by Everest.

After import, enable JIT for that running app and choose **Run Celeste**. Keep
Cabrillo open for the first preparation. Later launches reuse the cache; the
original download on your computer is unchanged. Upgrading from build52 can
prepare the already retained standard original files without another ZIP.

To change editions, finish the game with normal Quit, close and relaunch Cabrillo,
then choose the new ZIP. Saves and mod choices keep their existing locations.
A failed or cancelled preparation keeps the previous selected edition. Importing
a desktop game ZIP does **not** import its saves; use Cabrillo's Saves tab for that.

## If Cabrillo rejects a ZIP

Download a clean covered package again. Do not add a DLL from another store,
rename a different game version, or overwrite your working desktop installation.
An unknown/modified code file, mixed FNA/Steamworks files, missing assets,
duplicates or a damaged ZIP can cause rejection. Export Cabrillo diagnostics
with the store/platform/version when reporting an unrecognized original package.

## Sources and attribution

Acquisition instructions and the supported-input investigation are adapted from
[Morro's guide](https://github.com/hmcneill46/morro-celeste/blob/cc02b0cc697bd620c0dc864d4af3c60d79a95e85/docs/CELESTE_INPUTS.md)
at commit `cc02b0cc697bd620c0dc864d4af3c60d79a95e85`, under its
[MIT licence](licenses/MORRO-LICENSE.txt). Cabrillo verifies its own imports and
uses its own JIT/Everest preparation; it does not bundle Morro's generated game.
