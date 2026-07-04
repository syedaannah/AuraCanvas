# AuraCanvas - AI Music Canvas

Draw with your hand in the air, and get a playlist that matches the mood of your sketch. Uses hand tracking to let you draw without touching anything, Google Gemini to figure out the mood of your drawing, and Deezer to build a matching playlist.

## What it does

1. Draw something using just your index finger
2. Open your palm and hold it — this sends your sketch to Gemini for mood analysis
3. A playlist matching that mood shows up on the right side of the screen
4. Make a fist to clear the canvas and start over

## Controls

| Gesture | What it does |
|---|---|
| Point with index finger | Draw |
| Open palm (hold for ~1.5 sec) | Analyze sketch and generate playlist |
| Two fingers up (index + middle) | Scroll through the playlist |
| Closed fist (hold) | Clear the canvas |

Hovering over a track in the playlist plays a short preview automatically.

## How to run it

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/AuraCanvas.git
cd AuraCanvas
```

**2. Set up a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install requirements**
```bash
pip install -r req.txt
```

**4. Add your Gemini API key**

Create a file named `.env` in the project folder with this line inside: GEMINI_API_KEY=your_key_here
You can get a free key from [Google AI Studio](https://aistudio.google.com/).

**5. Run the app**
## Built with

- OpenCV + MediaPipe — hand tracking
- Google Gemini API — mood interpretation
- Deezer API — playlist generation
- Pygame — audio playback

## Notes

- Needs decent lighting for hand tracking to work well
- Gemini's free tier has a daily request limit, so heavy testing can temporarily block new sketches
