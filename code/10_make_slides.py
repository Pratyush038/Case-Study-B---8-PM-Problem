# Builds slides/8pm_problem_slides.pptx (10 slides, one idea each).

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
BLANK = prs.slide_layouts[6]
DARK = RGBColor(0x22, 0x22, 0x22)
BLUE = RGBColor(0x38, 0x6C, 0xB0)


def text_box(slide, text, left, top, width, height, size=20, bold=False, color=DARK):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    box.text_frame.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        p = box.text_frame.paragraphs[0] if i == 0 else box.text_frame.add_paragraph()
        p.text = line
        p.font.size, p.font.bold, p.font.color.rgb = Pt(size), bold, color
        p.space_after = Pt(8)


def slide(title, bullets="", image=None, note=""):
    s = prs.slides.add_slide(BLANK)
    text_box(s, title, 0.5, 0.3, 12.3, 1.0, size=30, bold=True, color=BLUE)
    if image:
        pic = s.shapes.add_picture(image, Inches(0.5), Inches(1.4), width=Inches(8.3))
        if pic.height > Inches(5.6):          # tall charts: shrink to fit the slide
            pic.width = int(pic.width * Inches(5.6) / pic.height)
            pic.height = Inches(5.6)
        text_box(s, bullets, 9.1, 1.6, 3.9, 5.5, size=17)
    else:
        text_box(s, bullets, 0.8, 1.6, 11.8, 5.5, size=22)
    if note:
        text_box(s, note, 0.5, 6.8, 12.3, 0.5, size=12, color=RGBColor(0x77, 0x77, 0x77))


slide("Bengaluru's worst air is 5 to 9 PM, and rain pushes the junction rush later",
      "1. On working days NO2 (our traffic sign) is 17% above normal from 5 to 8 PM. The morning rush barely shows.\n"
      "2. Evenings are dirtiest from January to April, not in the monsoon.\n"
      "3. Rain halves PM2.5, but at Silk Board it moves the NO2 peak from 5 PM to 9 PM.\n\n"
      "We ask for 5 to 9 PM alerts in Jan to Apr, and a rain-day plan for the junctions.",
      note="Rahul Patnaik, Vishal P Joy, Ansh Ravi Kashyap, Pratyush RB. Bengaluru, Oct 2025 to Oct 2026")

slide("The question",
      "When is Bengaluru's evening pollution rush at its worst, and does rain make it worse or push it later?\n\n"
      "It matters because office hours, metro trains, rider rules and pollution alerts are all about timing.\n\n"
      "No open hourly traffic data exists, so we use NO2 (mostly vehicle exhaust) as the traffic signal.")

slide("Four sources, 1.35 million rows",
      "Air quality from 6 CPCB and KSPCB stations, every 15 minutes (OpenAQ, CSV)\n"
      "Hourly rain from the Open-Meteo API (JSON)\n"
      "r/bangalore post titles from the Arctic Shift API (JSON, text)\n"
      "Karnataka holidays, typed in by hand\n\n"
      "1,800 files and 1.35M rows (volume), about 216 readings an hour (velocity)\n"
      "3 different time formats (variety). Lining up the hour was the hardest part.")

slide("The sensors are messy, so we cleaned with clear rules",
      "2,186 zeros and 23 readings of 999+ removed (one said 15,536)\n\n"
      "Stuck sensors: same value for 4+ hours removed\n\n"
      "Spikes at one station only removed, city-wide spikes (Deepavali) kept\n\n"
      "Gaps up to 3 hours filled, longer gaps left empty",
      image="charts/01_gap_chart.png")

slide("The evening is the real rush, every day of the week",
      "NO2 on working days\n5 to 8 PM is 117% of normal\n7 to 10 AM is 96%\nBefore dawn is 92%\n\n"
      "After sunset the air stops mixing upward, so exhaust gets trapped near the ground.",
      image="charts/02_heatmap_no2.png")

slide("Rain moves the rush later at junctions and washes PM2.5 down",
      "Monsoon working days, 24 rainy vs 15 dry evenings\n\n"
      "PM2.5 falls to half of normal\n\n"
      "NO2 peak moves from about 7 PM to 9 PM\n\n"
      "Mostly Silk Board, where 8 to 10 PM NO2 rose from 61% to 92% of normal",
      image="charts/03_rain_vs_dry.png",
      note="A link, not proof. Small sample and no traffic counts.")

slide("December to April evenings are the worst of the year",
      "March evenings had about 2x normal NO2\n\n"
      "Dec to Mar had about 1.5x normal PM2.5\n\n"
      "July and August are the cleanest\n\n"
      "Deepavali night hit 4x normal PM2.5",
      image="charts/07_months.png")

slide("What the city can do",
      "1. Pollution alerts from 5 to 9 PM on working days, January to April, and every Deepavali night.\n\n"
      "2. A rain-day plan when evening rain is forecast, with staggered exit times near Silk Board and Hebbal, "
      "extra metro trains 5 to 9 PM, slower targets for delivery riders.\n\n"
      "3. Fix the sensors first. Every station missed at least a fifth of its hours.")

slide("How far you can trust this",
      "Only 6 stations (4 in the city index). Whitefield and Electronic City are not covered.\n\n"
      "NO2 is a sign of traffic, not a traffic count.\n\n"
      "22% to 62% of hours missing. The rain effect rests mostly on one station.\n\n"
      "Reddit posters are young and online, not the whole city.")

slide("What we would do with better data",
      "Hourly traffic counts from Bengaluru Traffic Police\n\n"
      "Hourly metro ridership from BMRCL\n\n"
      "Food-delivery order times to see the Friday 8 PM peak directly\n\n"
      "More stations in the east and the outskirts\n\n"
      "Thank you. Questions?")

prs.save("slides/8pm_problem_slides.pptx")
print("saved", len(prs.slides), "slides")
