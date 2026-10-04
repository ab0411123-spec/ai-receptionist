
from __future__ import annotations

import time
from pathlib import Path

import cv2
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Campus Navigation",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VIDEOS_DIR = BASE_DIR / "videos"
FRAMES_DIR = BASE_DIR / "frames"

OFFICE_VIDEO = VIDEOS_DIR / "reception_to_office.mp4"
PRINCIPAL_VIDEO = VIDEOS_DIR / "reception_to_principal.mp4"

OFFICE_FRAMES = FRAMES_DIR / "reception_to_office"
PRINCIPAL_FRAMES = FRAMES_DIR / "reception_to_principal"


# ============================================================
# NAVIGATION SETTINGS
# ============================================================

# Extract approximately one frame every N seconds.
#
# Example:
# 60 FPS video + FRAME_INTERVAL = 5 seconds
# = approximately 1 navigation image every 5 seconds.
#
# Change to 0.5 for more frames.
# Change to 2.0 for fewer frames.

# INTERNAL SETTING — not shown in the app UI.
FRAME_INTERVAL = 5.0

# JPEG quality for extracted images
JPEG_QUALITY = 85


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GOLD + BLACK THEME
       ======================================================== */

    :root {
        --gold: #D4AF37;
        --gold-light: #F5D76E;
        --gold-dark: #B8860B;
        --black: #000000;
        --black-card: #0D0D0D;
        --white: #FFFFFF;
        --muted: #C8C8C8;
    }

    /* Main website background */
    .stApp,
    [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stHeader"] {
        background: #000000 !important;
    }

    [data-testid="stSidebar"] {
        background: #050505 !important;
    }

    /* General text */
    html, body, p, label, span, div {
        color: #FFFFFF;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
    }

    .title {
        text-align: center;
        font-size: 38px;
        font-weight: 800;
        color: #D4AF37 !important;
        text-shadow: 0 0 12px rgba(212, 175, 55, 0.25);
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 19px;
        color: #F5D76E !important;
        margin-bottom: 25px;
    }

    /* Cards */
    .route-card {
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #D4AF37;
        background: #0D0D0D;
        box-shadow: 0 0 18px rgba(212, 175, 55, 0.12);
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .route-title {
        font-size: 25px;
        font-weight: 700;
        color: #D4AF37 !important;
    }

    .step-text {
        text-align: center;
        font-size: 22px;
        font-weight: 600;
        color: #F5D76E !important;
        padding: 12px;
    }

    .destination-text {
        text-align: center;
        font-size: 26px;
        font-weight: 700;
        color: #D4AF37 !important;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .info-text {
        text-align: center;
        font-size: 17px;
        color: #FFFFFF !important;
    }

    /* ========================================================
       LARGE GOLD DROPDOWN
       ======================================================== */

    div[data-testid="stSelectbox"] {
        margin-top: 8px;
        margin-bottom: 22px;
    }

    div[data-testid="stSelectbox"] label {
        color: #D4AF37 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
    }

    div[data-testid="stSelectbox"] > div > div {
        background: #0D0D0D !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 12px !important;
        min-height: 62px !important;
        box-shadow: 0 0 12px rgba(212, 175, 55, 0.15);
    }

    div[data-testid="stSelectbox"] [role="combobox"] {
        color: #FFFFFF !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        min-height: 58px !important;
        padding: 10px 16px !important;
    }

    div[data-testid="stSelectbox"] svg {
        fill: #D4AF37 !important;
        color: #D4AF37 !important;
    }

    /* Dropdown menu */
    div[role="listbox"] {
        background: #0D0D0D !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 12px !important;
    }

    div[role="option"] {
        background: #0D0D0D !important;
        color: #FFFFFF !important;
        font-size: 19px !important;
        padding: 16px 18px !important;
        min-height: 54px !important;
    }

    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background: #D4AF37 !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* ========================================================
       GOLD BUTTONS
       ======================================================== */

    div.stButton > button {
        background: #D4AF37 !important;
        color: #000000 !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 12px !important;
        min-height: 58px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.18);
        transition: all 0.2s ease-in-out;
    }

    div.stButton > button:hover {
        background: #F5D76E !important;
        color: #000000 !important;
        border-color: #F5D76E !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(212, 175, 55, 0.30);
    }

    div.stButton > button:disabled {
        background: #3A321E !important;
        color: #8D7B43 !important;
        border-color: #5A4A24 !important;
    }

    /* Progress bar */
    div[data-testid="stProgress"] > div > div {
        background-color: #D4AF37 !important;
    }

    div[data-testid="stProgress"] > div {
        background-color: #242424 !important;
    }

    /* Alerts / success box */
    div[data-testid="stAlert"] {
        background: #0D0D0D !important;
        border: 1px solid #D4AF37 !important;
    }

    /* Divider */
    hr {
        border-color: #D4AF37 !important;
        opacity: 0.45;
    }

    /* Footer / captions */
    [data-testid="stCaptionContainer"] {
        color: #BDBDBD !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "route_name" not in st.session_state:
    st.session_state.route_name = None

if "current_frame" not in st.session_state:
    st.session_state.current_frame = 0

if "frames" not in st.session_state:
    st.session_state.frames = []

if "frame_generation_message" not in st.session_state:
    st.session_state.frame_generation_message = ""


# ============================================================
# CREATE DIRECTORIES
# ============================================================

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

OFFICE_FRAMES.mkdir(parents=True, exist_ok=True)
PRINCIPAL_FRAMES.mkdir(parents=True, exist_ok=True)


# ============================================================
# ROUTE INFORMATION
# ============================================================

ROUTES = {
    "Reception → Office": {
        "video": OFFICE_VIDEO,
        "frames": OFFICE_FRAMES,
        "destination": "College Office",
        "icon": "🏢",
    },

    "Reception → Principal": {
        "video": PRINCIPAL_VIDEO,
        "frames": PRINCIPAL_FRAMES,
        "destination": "Principal Office",
        "icon": "👨‍💼",
    },
}


# ============================================================
# GET EXISTING FRAMES
# ============================================================

def get_existing_frames(frame_folder: Path) -> list[Path]:
    """
    Return all extracted JPG frames in numerical order.
    """

    if not frame_folder.exists():
        return []

    frames = list(frame_folder.glob("frame_*.jpg"))

    frames.sort(
        key=lambda path: int(
            path.stem.split("_")[-1]
        )
    )

    return frames


# ============================================================
# EXTRACT VIDEO FRAMES
# ============================================================

def extract_frames(
    video_path: Path,
    output_folder: Path,
    interval_seconds: float = FRAME_INTERVAL,
) -> list[Path]:
    """
    Extract frames from a video.

    Frames are extracted approximately every interval_seconds.

    Example:
        interval_seconds = 1.0
        → approximately one frame per second.
    """

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Check video
    # --------------------------------------------------------

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found:\n{video_path}"
        )

    # --------------------------------------------------------
    # Remove old frames
    # --------------------------------------------------------

    for old_frame in output_folder.glob("frame_*.jpg"):
        try:
            old_frame.unlink()
        except Exception:
            pass

    # --------------------------------------------------------
    # Open video
    # --------------------------------------------------------

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video:\n{video_path}"
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    duration = 0

    if fps and fps > 0:
        duration = total_frames / fps

    # --------------------------------------------------------
    # Determine frame interval
    # --------------------------------------------------------

    if fps <= 0:
        fps = 30

    frame_step = max(
        1,
        int(round(fps * interval_seconds))
    )

    # --------------------------------------------------------
    # Extract
    # --------------------------------------------------------

    frame_paths = []

    frame_number = 0
    saved_number = 1

    progress = st.progress(
        0,
        text="Preparing video..."
    )

    while True:

        success, frame = cap.read()

        if not success:
            break

        # Save selected frames
        if frame_number % frame_step == 0:

            output_path = (
                output_folder
                / f"frame_{saved_number:04d}.jpg"
            )

            success_write = cv2.imwrite(
                str(output_path),
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    JPEG_QUALITY,
                ],
            )

            if success_write:
                frame_paths.append(output_path)
                saved_number += 1

        # Update progress
        if total_frames > 0:

            progress_value = min(
                frame_number / total_frames,
                1.0
            )

            progress.progress(
                progress_value,
                text=(
                    f"Extracting frames... "
                    f"{frame_number:,} / "
                    f"{total_frames:,}"
                ),
            )

        frame_number += 1

    cap.release()

    progress.progress(
        1.0,
        text="Frame extraction completed."
    )

    time.sleep(0.3)

    progress.empty()

    return frame_paths


# ============================================================
# GET OR CREATE FRAMES
# ============================================================

def prepare_route_frames(route_name: str) -> list[Path]:

    route = ROUTES[route_name]

    video_path = route["video"]
    frame_folder = route["frames"]

    # --------------------------------------------------------
    # Check video exists
    # --------------------------------------------------------

    if not video_path.exists():

        st.error(
            f"""
            Video file was not found:

            `{video_path}`

            Please place the MP4 file in the `videos` folder.
            """
        )

        return []

    # --------------------------------------------------------
    # Check existing frames
    # --------------------------------------------------------

    existing_frames = get_existing_frames(
        frame_folder
    )

    if existing_frames:

        return existing_frames

    # --------------------------------------------------------
    # Extract frames automatically
    # --------------------------------------------------------

    st.info(
        f"Preparing navigation frames from "
        f"`{video_path.name}`..."
    )

    try:

        frames = extract_frames(
            video_path,
            frame_folder,
            FRAME_INTERVAL,
        )

        return frames

    except Exception as error:

        st.error(
            f"Frame extraction failed:\n\n{error}"
        )

        return []


# ============================================================
# DELETE / REBUILD FRAMES
# ============================================================

def delete_frames(frame_folder: Path):

    if frame_folder.exists():

        for frame in frame_folder.glob(
            "frame_*.jpg"
        ):
            try:
                frame.unlink()
            except Exception:
                pass


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🗺️ Campus Navigation</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        St. Mary's Polytechnic College, Palakkad
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STARTING POINT
# ============================================================

st.markdown(
    """
    <div class="route-card">

    <div class="destination-text">
        📍 Starting Point: Reception
    </div>

    <div class="info-text">
        Select your destination below.
    </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DESTINATION SELECTION
# ============================================================

st.subheader("Where do you want to go?")

route_options = list(ROUTES.keys())

selected_route = st.selectbox(
    "Select destination",
    route_options,
)


# ============================================================
# RESET WHEN ROUTE CHANGES
# ============================================================

if st.session_state.route_name != selected_route:

    st.session_state.route_name = selected_route
    st.session_state.current_frame = 0
    st.session_state.frames = []


route = ROUTES[selected_route]

video_path = route["video"]
frame_folder = route["frames"]
destination = route["destination"]
icon = route["icon"]


# ============================================================
# ROUTE INFORMATION
# ============================================================

st.markdown(
    f"""
    <div class="route-card">

    <div class="route-title">
        {icon} {selected_route}
    </div>

    <p>
        <b>From:</b> Reception
    </p>

    <p>
        <b>To:</b> {destination}
    </p>

    <p>
        <b>Navigation video:</b> {video_path.name}
    </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# VIDEO STATUS
# ============================================================

if not video_path.exists():

    st.error(
        f"""
        ❌ Video not found.

        Expected location:

        `{video_path}`

        Please create the `videos` folder and put the
        correct MP4 file inside it.
        """
    )

    st.stop()


# ============================================================
# LOAD / EXTRACT FRAMES
# ============================================================

if not st.session_state.frames:

    frames = prepare_route_frames(
        selected_route
    )

    st.session_state.frames = frames


frames = st.session_state.frames


# ============================================================
# NO FRAMES
# ============================================================

if not frames:

    st.error(
        "No navigation frames are available."
    )

    st.stop()


# ============================================================
# FRAME INDEX SAFETY
# ============================================================

if (
    st.session_state.current_frame < 0
):
    st.session_state.current_frame = 0


if (
    st.session_state.current_frame
    >= len(frames)
):
    st.session_state.current_frame = len(frames) - 1


current_index = (
    st.session_state.current_frame
)

current_frame_path = frames[current_index]


# ============================================================
# PROGRESS
# ============================================================

progress_value = (
    (current_index + 1)
    / len(frames)
)

st.progress(
    progress_value,
    text=(
        f"Navigation Step "
        f"{current_index + 1} of {len(frames)}"
    ),
)


# ============================================================
# CURRENT FRAME
# ============================================================

st.markdown(
    f"""
    <div class="step-text">
        🚶 Follow this path
    </div>
    """,
    unsafe_allow_html=True,
)


# Display ONLY the navigation frame in a mobile-phone portrait size.
# The rest of the application keeps its existing desktop/wide layout.
st.markdown(
    """
    <style>
    .mobile-navigation-frame {
        width: 360px;
        height: 640px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border-radius: 18px;
        border: 2px solid #D4AF37;
        background: #000;
    }

    .mobile-navigation-frame img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    @media (max-width: 600px) {
        .mobile-navigation-frame {
            width: min(360px, 92vw);
            height: min(640px, 164vw);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

import base64

with open(current_frame_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

st.markdown(
    f"""
    <div class="mobile-navigation-frame">
        <img
            src="data:image/jpeg;base64,{image_base64}"
            alt="Navigation frame"
        />
    </div>
    <div style="text-align:center; margin-top:10px; font-size:16px;">
        {selected_route} • Step {current_index + 1}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NAVIGATION BUTTONS
# ============================================================

col1, col2, col3 = st.columns(3)


with col1:

    previous_disabled = (
        current_index == 0
    )

    if st.button(
        "⬅️ Previous",
        use_container_width=True,
        disabled=previous_disabled,
    ):

        st.session_state.current_frame -= 1
        st.rerun()


with col2:

    if st.button(
        "🔄 Restart",
        use_container_width=True,
    ):

        st.session_state.current_frame = 0
        st.rerun()


with col3:

    next_disabled = (
        current_index >= len(frames) - 1
    )

    if st.button(
        "Next ➡️",
        use_container_width=True,
        disabled=next_disabled,
    ):

        st.session_state.current_frame += 1
        st.rerun()


# ============================================================
# ARRIVAL MESSAGE
# ============================================================

if current_index == len(frames) - 1:

    st.success(
        f"🎯 You have reached {destination}."
    )


# ============================================================
# ROUTE DETAILS
# ============================================================

st.divider()

st.subheader("🧭 Route Details")

st.write(
    f"**Starting point:** Reception"
)

st.write(
    f"**Destination:** {destination}"
)

st.write(
    f"**Navigation frames:** {len(frames)}"
)



# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Campus Navigation • "
    "Reception-based indoor navigation"
)

