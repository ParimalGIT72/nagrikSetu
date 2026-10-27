#!/usr/bin/env python3
"""
scripts/generate_eval_dataset.py

Generates a reproducible multilingual civic evaluation dataset
for Nagrik Setu Phase 2 benchmark evaluation.

Dataset composition:
  - English clean (60 cases)
  - Marathi Devanagari clean (60 cases)
  - Hindi Devanagari clean (60 cases)
  - Code-mixed Marathi-English (40 cases)  — includes non-marker-set words
  - Code-mixed Hindi-English (10 cases)    — new category
  - Romanized Hindi, no English (5 cases)  — new category
  - Romanized Marathi, no English (5 cases) — explicit category
  - Normalization stress tests (30 cases)  — independently verified expected outputs
  - Edge cases (20 cases)                  — empty, short, ambiguous, mixed-script, ALL-CAPS
  Total: ~290 cases

Label provenance field values:
  - "unambiguous": language/script determinable from Unicode ranges and vocabulary
  - "curated": label assigned by developer with linguistic justification
  - "review_needed": genuinely ambiguous; label is best-effort, may need expert review

HOW TO REGENERATE:
  python scripts/generate_eval_dataset.py
  This overwrites ml/data/multilingual_eval_300.json deterministically.
"""

import json
from pathlib import Path

DEST_PATH = Path(__file__).resolve().parent.parent / "ml" / "data" / "multilingual_eval_300.json"

CATEGORIES = [
    "roads", "garbage", "water_supply", "street_light", "drainage",
    "traffic", "electricity", "public_transport", "noise", "illegal_dumping"
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 1: CLEAN ENGLISH TEMPLATES (60)
# Format: (category, original_text, expected_normalized_text)
# For clean inputs, expected_normalized_text == original_text because
# the normalizer should not alter well-formed text.
# ──────────────────────────────────────────────────────────────────────
ENGLISH_COMPLAINTS = [
    ("roads", "There is a large pothole near FC Road causing accidents.", "There is a large pothole near FC Road causing accidents."),
    ("roads", "Deep crater on Karve Road after heavy monsoon rains.", "Deep crater on Karve Road after heavy monsoon rains."),
    ("roads", "Road resurfacing is urgently needed on Baner Pashan link road.", "Road resurfacing is urgently needed on Baner Pashan link road."),
    ("roads", "Dangerous speed breaker without white paint marks near university gate.", "Dangerous speed breaker without white paint marks near university gate."),
    ("roads", "Asphalt washed away on Sinhagad road creating flying pebbles.", "Asphalt washed away on Sinhagad road creating flying pebbles."),
    ("roads", "Multiple potholes outside Pune station autorickshaw stand.", "Multiple potholes outside Pune station autorickshaw stand."),
    ("roads", "Manhole cover is uneven and raised above road level on JM Road.", "Manhole cover is uneven and raised above road level on JM Road."),
    ("roads", "Unpaved side road in Hadapsar creating severe dust and skidding.", "Unpaved side road in Hadapsar creating severe dust and skidding."),
    ("garbage", "Overflowing waste container at Kothrud depot spreading foul smell.", "Overflowing waste container at Kothrud depot spreading foul smell."),
    ("garbage", "Garbage collection truck has not visited Bavdhan for three days.", "Garbage collection truck has not visited Bavdhan for three days."),
    ("garbage", "Stray cattle feeding on open trash heap in Shivajinagar.", "Stray cattle feeding on open trash heap in Shivajinagar."),
    ("garbage", "Plastic waste and wet garbage rotting near municipal school.", "Plastic waste and wet garbage rotting near municipal school."),
    ("garbage", "Waste sorting bin broken and scattered across pedestrian pavement.", "Waste sorting bin broken and scattered across pedestrian pavement."),
    ("garbage", "Illegal dumping of residential food waste near Katraj lake garden.", "Illegal dumping of residential food waste near Katraj lake garden."),
    ("water_supply", "Low pressure tap water supply in Aundh residential society.", "Low pressure tap water supply in Aundh residential society."),
    ("water_supply", "Contaminated muddy water flowing through drinking water pipeline.", "Contaminated muddy water flowing through drinking water pipeline."),
    ("water_supply", "Main supply pipe leakage wasting gallons of drinking water on road.", "Main supply pipe leakage wasting gallons of drinking water on road."),
    ("water_supply", "No municipal water received in Warje for the past 48 hours.", "No municipal water received in Warje for the past 48 hours."),
    ("water_supply", "Irregular water supply timings causing hardship to senior citizens.", "Irregular water supply timings causing hardship to senior citizens."),
    ("water_supply", "Water valve malfunctioning and overflowing into nearby gutters.", "Water valve malfunctioning and overflowing into nearby gutters."),
    ("street_light", "Street lights not functioning on Viman Nagar main road.", "Street lights not functioning on Viman Nagar main road."),
    ("street_light", "Complete darkness on internal lane of Tingre Nagar for one week.", "Complete darkness on internal lane of Tingre Nagar for one week."),
    ("street_light", "Street light pole bent precariously after truck collision.", "Street light pole bent precariously after truck collision."),
    ("street_light", "Exposed wiring on electrical lamp post posing safety hazard to children.", "Exposed wiring on electrical lamp post posing safety hazard to children."),
    ("street_light", "Street light blinking continuously causing irritation to residents.", "Street light blinking continuously causing irritation to residents."),
    ("street_light", "Lights turned on during daylight hours leading to electricity wastage.", "Lights turned on during daylight hours leading to electricity wastage."),
    ("drainage", "Open gutter overflowing with black sewage on Paud Road.", "Open gutter overflowing with black sewage on Paud Road."),
    ("drainage", "Storm water drain completely choked with silt and plastic debris.", "Storm water drain completely choked with silt and plastic debris."),
    ("drainage", "Missing storm drain cover creating fatal death trap for pedestrians.", "Missing storm drain cover creating fatal death trap for pedestrians."),
    ("drainage", "Drainage inspection chamber cracked and emitting nauseating fumes.", "Drainage inspection chamber cracked and emitting nauseating fumes."),
    ("drainage", "Sewage backing up into ground floor apartments during rainfall.", "Sewage backing up into ground floor apartments during rainfall."),
    ("drainage", "Clogged roadside culvert flooding nearby shops and commercial spaces.", "Clogged roadside culvert flooding nearby shops and commercial spaces."),
    ("traffic", "Traffic signal at Swargate junction malfunctioning and showing yellow.", "Traffic signal at Swargate junction malfunctioning and showing yellow."),
    ("traffic", "Illegal vehicle parking blocking entire left turn at busy square.", "Illegal vehicle parking blocking entire left turn at busy square."),
    ("traffic", "Commercial auto rickshaws blocking city bus stop entrance.", "Commercial auto rickshaws blocking city bus stop entrance."),
    ("traffic", "Missing pedestrian zebra crossing markings at school intersection.", "Missing pedestrian zebra crossing markings at school intersection."),
    ("traffic", "Extreme traffic bottleneck due to unauthorized road vendors.", "Extreme traffic bottleneck due to unauthorized road vendors."),
    ("traffic", "Lack of traffic police personnel during morning peak school rush.", "Lack of traffic police personnel during morning peak school rush."),
    ("electricity", "Frequent unannounced power outages in Model Colony area.", "Frequent unannounced power outages in Model Colony area."),
    ("electricity", "High voltage fluctuation damaged domestic refrigerator and television.", "High voltage fluctuation damaged domestic refrigerator and television."),
    ("electricity", "Low hanging high tension cable dangerously touching apartment balcony.", "Low hanging high tension cable dangerously touching apartment balcony."),
    ("electricity", "Substation transformer sparking loudly with smoke during drizzle.", "Substation transformer sparking loudly with smoke during drizzle."),
    ("electricity", "Feeder pillar box left open with live wire exposed on footpath.", "Feeder pillar box left open with live wire exposed on footpath."),
    ("electricity", "Underground cable fault leaving block without power for over 12 hours.", "Underground cable fault leaving block without power for over 12 hours."),
    ("public_transport", "PMPML city bus arrived forty minutes late during morning office rush.", "PMPML city bus arrived forty minutes late during morning office rush."),
    ("public_transport", "Broken passenger seats and shattered glass on route twenty-four bus.", "Broken passenger seats and shattered glass on route twenty-four bus."),
    ("public_transport", "Bus driver refused to halt vehicle at designated passenger stop.", "Bus driver refused to halt vehicle at designated passenger stop."),
    ("public_transport", "Bus conductor overcharged ticket fare and misbehaved with student.", "Bus conductor overcharged ticket fare and misbehaved with student."),
    ("public_transport", "Damaged bus shelter roof leaking rainwater directly onto passengers.", "Damaged bus shelter roof leaking rainwater directly onto passengers."),
    ("public_transport", "Digital display board at Swargate terminal showing wrong bus timetable.", "Digital display board at Swargate terminal showing wrong bus timetable."),
    ("noise", "Loud music and DJ speakers operating past midnight near residential society.", "Loud music and DJ speakers operating past midnight near residential society."),
    ("noise", "Illegal industrial generator creating excessive noise vibrations throughout night.", "Illegal industrial generator creating excessive noise vibrations throughout night."),
    ("noise", "Heavy trucks using prohibited multi-tone air horns near hospital zone.", "Heavy trucks using prohibited multi-tone air horns near hospital zone."),
    ("noise", "Construction activity with concrete mixers running continuously at 2 AM.", "Construction activity with concrete mixers running continuously at 2 AM."),
    ("noise", "Wedding procession blocking ambulance route with deafening firecrackers.", "Wedding procession blocking ambulance route with deafening firecrackers."),
    ("noise", "Commercial workshop hammering metal sheets in declared silence zone.", "Commercial workshop hammering metal sheets in declared silence zone."),
    ("illegal_dumping", "Construction debris and debris sacks dumped secretly on riverbed.", "Construction debris and debris sacks dumped secretly on riverbed."),
    ("illegal_dumping", "Private hospital dumping hazardous medical waste in open vacant plot.", "Private hospital dumping hazardous medical waste in open vacant plot."),
    ("illegal_dumping", "Tractor trolley unloading concrete rubble across public footpath.", "Tractor trolley unloading concrete rubble across public footpath."),
    ("illegal_dumping", "Chemical slurry poured into storm water line under darkness.", "Chemical slurry poured into storm water line under darkness."),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 2: CLEAN MARATHI DEVANAGARI TEMPLATES (60)
# ──────────────────────────────────────────────────────────────────────
MARATHI_COMPLAINTS = [
    ("roads", "रस्त्यावर खूप मोठा खड्डा पडला असून अपघाताचा धोका आहे.", "रस्त्यावर खूप मोठा खड्डा पडला असून अपघाताचा धोका आहे."),
    ("roads", "कर्वे रस्त्यावर पावसाने डांबर वाहून गेले असून खोल खड्डे पडले आहेत.", "कर्वे रस्त्यावर पावसाने डांबर वाहून गेले असून खोल खड्डे पडले आहेत."),
    ("roads", "बाणेर रस्त्यावरील गतिरोधकावर पांढरे पट्टे नसल्याने वाहनचालक पडत आहेत.", "बाणेर रस्त्यावरील गतिरोधकावर पांढरे पट्टे नसल्याने वाहनचालक पडत आहेत."),
    ("roads", "सिंहगड रस्त्यावर रस्त्याचे काम अर्धवट सोडल्याने खडी उडत आहे.", "सिंहगड रस्त्यावर रस्त्याचे काम अर्धवट सोडल्याने खडी उडत आहे."),
    ("roads", "पुणे स्टेशन बाहेरील रिक्षा स्टँड समोर चिखल आणि मोठा खड्डा झाला आहे.", "पुणे स्टेशन बाहेरील रिक्षा स्टँड समोर चिखल आणि मोठा खड्डा झाला आहे."),
    ("roads", "जेएम रस्त्यावर ड्रेनेजचे झाकण रस्त्याच्या पातळीपेक्षा उंच आहे.", "जेएम रस्त्यावर ड्रेनेजचे झाकण रस्त्याच्या पातळीपेक्षा उंच आहे."),
    ("roads", "हडपसर मधील अंतर्गत रस्ता कच्चा असल्याने दुचाकी घसरत आहेत.", "हडपसर मधील अंतर्गत रस्ता कच्चा असल्याने दुचाकी घसरत आहेत."),
    ("garbage", "कोथरूड आगाराजवळ कचरा कुंडी भरून वाहते आहे आणि दुर्गंधी पसरली आहे.", "कोथरूड आगाराजवळ कचरा कुंडी भरून वाहते आहे आणि दुर्गंधी पसरली आहे."),
    ("garbage", "बावधन परिसरात मागील तीन दिवसांपासून घंटागाडी आलेली नाही.", "बावधन परिसरात मागील तीन दिवसांपासून घंटागाडी आलेली नाही."),
    ("garbage", "शिवाजीनगर येथील कचऱ्याच्या ढिगाऱ्यात भटकी जनावरे फिरत आहेत.", "शिवाजीनगर येथील कचऱ्याच्या ढिगाऱ्यात भटकी जनावरे फिरत आहेत."),
    ("garbage", "शाळेजवळ ओला आणि सुका कचरा कुजत असल्याने आरोग्यास धोका आहे.", "शाळेजवळ ओला आणि सुका कचरा कुजत असल्याने आरोग्यास धोका आहे."),
    ("garbage", "कात्रज तलावाजवळ नागरिक प्लास्टिक कचरा उघड्यावर टाकत आहेत.", "कात्रज तलावाजवळ नागरिक प्लास्टिक कचरा उघड्यावर टाकत आहेत."),
    ("garbage", "भाजी मंडई परिसरात नियमित कचरा उचलला जात नाही.", "भाजी मंडई परिसरात नियमित कचरा उचलला जात नाही."),
    ("water_supply", "औंध परिसरातील सोसायट्यांमध्ये कमी दाबाने पाणीपुरवठा होत आहे.", "औंध परिसरातील सोसायट्यांमध्ये कमी दाबाने पाणीपुरवठा होत आहे."),
    ("water_supply", "पिण्याच्या पाण्याच्या नळाला गढूळ आणि दुर्गंधीयुक्त पाणी येत आहे.", "पिण्याच्या पाण्याच्या नळाला गढूळ आणि दुर्गंधीयुक्त पाणी येत आहे."),
    ("water_supply", "वारजे भागात मुख्य जलवाहिनी फुटून लाखो लिटर पाणी वाया जात आहे.", "वारजे भागात मुख्य जलवाहिनी फुटून लाखो लिटर पाणी वाया जात आहे."),
    ("water_supply", "गेल्या दोन दिवसांपासून नळाला अजिबात पाणी आलेले नाही.", "गेल्या दोन दिवसांपासून नळाला अजिबात पाणी आलेले नाही."),
    ("water_supply", "धनकवडी परिसरात पाणीपुरवठ्याची वेळ नियमित नसल्याने हाल होत आहेत.", "धनकवडी परिसरात पाणीपुरवठ्याची वेळ नियमित नसल्याने हाल होत आहेत."),
    ("water_supply", "वॉल्व्ह गळतीमुळे रस्त्यावर पाणी साठून तळे निर्माण झाले आहे.", "वॉल्व्ह गळतीमुळे रस्त्यावर पाणी साठून तळे निर्माण झाले आहे."),
    ("street_light", "विमान नगर मुख्य रस्त्यावरील पथदिवे अनेक दिवसांपासून बंद आहेत.", "विमान नगर मुख्य रस्त्यावरील पथदिवे अनेक दिवसांपासून बंद आहेत."),
    ("street_light", "टिंगरे नगर अंतर्गत गल्लीत अंधार असल्यामुळे महिलांना भीती वाटते.", "टिंगरे नगर अंतर्गत गल्लीत अंधार असल्यामुळे महिलांना भीती वाटते."),
    ("street_light", "अपघातामुळे विजेचा खांब वाकला असून खाली पडण्याची शक्यता आहे.", "अपघातामुळे विजेचा खांब वाकला असून खाली पडण्याची शक्यता आहे."),
    ("street_light", "पथदिव्यांच्या उघड्या तारांमुळे लहान मुलांना विजेचा धक्का बसू शकतो.", "पथदिव्यांच्या उघड्या तारांमुळे लहान मुलांना विजेचा धक्का बसू शकतो."),
    ("street_light", "दिवसाही पथदिवे चालू राहिल्याने विजेचा अपव्यय होत आहे.", "दिवसाही पथदिवे चालू राहिल्याने विजेचा अपव्यय होत आहे."),
    ("street_light", "झाडांच्या फांद्या वाढल्याने पथदिव्यांचा प्रकाश रस्त्यावर पडत नाही.", "झाडांच्या फांद्या वाढल्याने पथदिव्यांचा प्रकाश रस्त्यावर पडत नाही."),
    ("drainage", "पौड रस्त्यावरील उघडे गटार तुंबले असून सांडपाणी रस्त्यावर येत आहे.", "पौड रस्त्यावरील उघडे गटार तुंबले असून सांडपाणी रस्त्यावर येत आहे."),
    ("drainage", "पावसाळी गटार गाळाने भरल्यामुळे पावसाचे पाणी घरात शिरले आहे.", "पावसाळी गटार गाळाने भरल्यामुळे पावसाचे पाणी घरात शिरले आहे."),
    ("drainage", "ड्रेनेज चेंबरचे झाकण तुटल्याने वाहने खड्ड्यात अडकत आहेत.", "ड्रेनेज चेंबरचे झाकण तुटल्याने वाहने खड्ड्यात अडकत आहेत."),
    ("drainage", "सांडपाणी वाहून नेणारी पाईप फुटल्याने भयानक दुर्गंधी सुटली आहे.", "सांडपाणी वाहून नेणारी पाईप फुटल्याने भयानक दुर्गंधी सुटली आहे."),
    ("drainage", "उघड्या गटारात डासांची पैदास वाढल्याने डेंग्यूचा प्रादुर्भाव वाढला आहे.", "उघड्या गटारात डासांची पैदास वाढल्याने डेंग्यूचा प्रादुर्भाव वाढला आहे."),
    ("drainage", "सफाई कर्मचाऱ्यांनी गटारातील गाळ काढून रस्त्यावरच टाकून दिला आहे.", "सफाई कर्मचाऱ्यांनी गटारातील गाळ काढून रस्त्यावरच टाकून दिला आहे."),
    ("traffic", "स्वारगेट चौकातील वाहतूक सिग्नल बंद असल्याने मोठी कोंडी झाली आहे.", "स्वारगेट चौकातील वाहतूक सिग्नल बंद असल्याने मोठी कोंडी झाली आहे."),
    ("traffic", "डाव्या बाजूला वळणाऱ्या रस्त्यावर बेकायदेशीर वाहने उभी केली जातात.", "डाव्या बाजूला वळणाऱ्या रस्त्यावर बेकायदेशीर वाहने उभी केली जातात."),
    ("traffic", "रिक्षाचालक बस स्टॉपच्या समोर वाहने लावून प्रवाशांना अडवतात.", "रिक्षाचालक बस स्टॉपच्या समोर वाहने लावून प्रवाशांना अडवतात."),
    ("traffic", "शाळेसमोरील चौकात झेब्रा क्रॉसिंग नसल्याने विद्यार्थ्यांना धोका आहे.", "शाळेसमोरील चौकात झेब्रा क्रॉसिंग नसल्याने विद्यार्थ्यांना धोका आहे."),
    ("traffic", "पादचारी मार्गावर फळविक्रेत्यांनी अतिक्रमण केल्याने रस्त्यावरून चालावे लागते.", "पादचारी मार्गावर फळविक्रेत्यांनी अतिक्रमण केल्याने रस्त्यावरून चालावे लागते."),
    ("traffic", "सकाळच्या गर्दीच्या वेळी चौकात वाहतूक पोलीस हजर नसतात.", "सकाळच्या गर्दीच्या वेळी चौकात वाहतूक पोलीस हजर नसतात."),
    ("electricity", "मॉडेल कॉलनी परिसरात वारंवार वीजपुरवठा खंडित होत आहे.", "मॉडेल कॉलनी परिसरात वारंवार वीजपुरवठा खंडित होत आहे."),
    ("electricity", "अचानक व्होल्टेज वाढल्यामुळे घरातील टीव्ही आणि फ्रीज जळून गेले.", "अचानक व्होल्टेज वाढल्यामुळे घरातील टीव्ही आणि फ्रीज जळून गेले."),
    ("electricity", "विजेच्या तारा घराच्या गॅलरीला धोकादायक पद्धतीने स्पर्श करत आहेत.", "विजेच्या तारा घराच्या गॅलरीला धोकादायक पद्धतीने स्पर्श करत आहेत."),
    ("electricity", "ट्रान्सफॉर्मरमधून ठिणग्या उडत असून मोठा आवाज येत आहे.", "ट्रान्सफॉर्मरमधून ठिणग्या उडत असून मोठा आवाज येत आहे."),
    ("electricity", "पादचारी मार्गावरील डीपी बॉक्सचे दार उघडे असून जिवंत तारा दिसत आहेत.", "पादचारी मार्गावरील डीपी बॉक्सचे दार उघडे असून जिवंत तारा दिसत आहेत."),
    ("electricity", "भूमिगत केबल खराब झाल्याने २४ तास वीज बंद होती.", "भूमिगत केबल खराब झाल्याने २४ तास वीज बंद होती."),
    ("public_transport", "पीएमपीएमएल बस वेळेवर न आल्यामुळे नोकरदारांचे हाल झाले.", "पीएमपीएमएल बस वेळेवर न आल्यामुळे नोकरदारांचे हाल झाले."),
    ("public_transport", "बसच्या खिडक्यांची तावदाने तुटलेली असून पावसाचे पाणी आत येते.", "बसच्या खिडक्यांची तावदाने तुटलेली असून पावसाचे पाणी आत येते."),
    ("public_transport", "चालकाने बस थांब्यावर न थांबवता पुढे निघून नेली.", "चालकाने बस थांब्यावर न थांबवता पुढे निघून नेली."),
    ("public_transport", "कंडक्टरने सुट्टे पैसे परत न देता प्रवाशांशी उद्धट वर्तन केले.", "कंडक्टरने सुट्टे पैसे परत न देता प्रवाशांशी उद्धट वर्तन केले."),
    ("public_transport", "बस थांब्याचे शेड तुटल्यामुळे प्रवाशांना उन्हात उभे राहावे लागते.", "बस थांब्याचे शेड तुटल्यामुळे प्रवाशांना उन्हात उभे राहावे लागते."),
    ("public_transport", "डिजिटल फलकावर बसच्या वेळापत्रकाची चुकीची माहिती दाखवली जात आहे.", "डिजिटल फलकावर बसच्या वेळापत्रकाची चुकीची माहिती दाखवली जात आहे."),
    ("noise", "मध्यरात्रीनंतरही परिसरात डीजेचे कर्कश आवाज सुरू आहेत.", "मध्यरात्रीनंतरही परिसरात डीजेचे कर्कश आवाज सुरू आहेत."),
    ("noise", "हॉस्पिटल परिसरात अवजड वाहनांचे प्रेशर हॉर्न सतत वाजत आहेत.", "हॉस्पिटल परिसरात अवजड वाहनांचे प्रेशर हॉर्न सतत वाजत आहेत."),
    ("noise", "निवासी भागात बेकायदेशीर कारखान्यातून रात्रभर यंत्रांचा आवाज येतो.", "निवासी भागात बेकायदेशीर कारखान्यातून रात्रभर यंत्रांचा आवाज येतो."),
    ("noise", "रात्री दोन वाजता इमारतीचे बांधकाम सुरू असल्याने झोप लागत नाही.", "रात्री दोन वाजता इमारतीचे बांधकाम सुरू असल्याने झोप लागत नाही."),
    ("noise", "लग्न मिरवणुकीत फटाके वाजवून रुग्णालयातील रुग्णांना त्रास दिला जात आहे.", "लग्न मिरवणुकीत फटाके वाजवून रुग्णालयातील रुग्णांना त्रास दिला जात आहे."),
    ("illegal_dumping", "मुळा मुठा नदीपात्रात रात्रीच्या वेळी बांधकामाचा राडारोडा टाकला जात आहे.", "मुळा मुठा नदीपात्रात रात्रीच्या वेळी बांधकामाचा राडारोडा टाकला जात आहे."),
    ("illegal_dumping", "मोकळ्या जागेत बायोमेडिकल कचरा फेकला जात असल्याने संसर्ग वाढू शकतो.", "मोकळ्या जागेत बायोमेडिकल कचरा फेकला जात असल्याने संसर्ग वाढू शकतो."),
    ("illegal_dumping", "टेकडीवर प्लास्टिक कारखान्यातील टाकाऊ माल बेकायदेशीरपणे टाकला आहे.", "टेकडीवर प्लास्टिक कारखान्यातील टाकाऊ माल बेकायदेशीरपणे टाकला आहे."),
    ("illegal_dumping", "रसायनयुक्त सांडपाणी रात्री टँकरने नाल्यामध्ये सोडले जात आहे.", "रसायनयुक्त सांडपाणी रात्री टँकरने नाल्यामध्ये सोडले जात आहे."),
    ("illegal_dumping", "पादचारी मार्गावर जुने टायर रचून ठेवल्याने आग लागण्याची भीती आहे.", "पादचारी मार्गावर जुने टायर रचून ठेवल्याने आग लागण्याची भीती आहे."),
    ("illegal_dumping", "सार्वजनिक बागेच्या कोपऱ्यात घराचे बांधकाम साहित्य फेकून दिले आहे.", "सार्वजनिक बागेच्या कोपऱ्यात घराचे बांधकाम साहित्य फेकून दिले आहे."),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 3: CLEAN HINDI DEVANAGARI TEMPLATES (60)
# ──────────────────────────────────────────────────────────────────────
HINDI_COMPLAINTS = [
    ("roads", "सड़क पर बहुत बड़ा गड्ढा है जिससे रोज दुर्घटनाएं हो रही हैं।", "सड़क पर बहुत बड़ा गड्ढा है जिससे रोज दुर्घटनाएं हो रही हैं।"),
    ("roads", "बारिश के बाद मुख्य सड़क का डामर बह गया और गहरे गड्ढे बन गए हैं।", "बारिश के बाद मुख्य सड़क का डामर बह गया और गहरे गड्ढे बन गए हैं।"),
    ("roads", "स्पीड ब्रेकर पर सफेद पट्टी न होने से रात में गाड़ियां फिसल रही हैं।", "स्पीड ब्रेकर पर सफेद पट्टी न होने से रात में गाड़ियां फिसल रही हैं।"),
    ("roads", "सड़क का काम अधूरा छोड़ दिया गया है जिससे गिट्टी उड़ रही है।", "सड़क का काम अधूरा छोड़ दिया गया है जिससे गिट्टी उड़ रही है।"),
    ("roads", "रेलवे स्टेशन के बाहर सड़क पर कीचड़ और भारी जलभराव है।", "रेलवे स्टेशन के बाहर सड़क पर कीचड़ और भारी जलभराव है।"),
    ("roads", "मैनहोल का ढक्कन सड़क की सतह से काफी ऊपर निकला हुआ है।", "मैनहोल का ढक्कन सड़क की सतह से काफी ऊपर निकला हुआ है।"),
    ("roads", "कच्ची सड़क होने के कारण धूल उड़ती है और सांस लेना मुश्किल हो गया है।", "कच्ची सड़क होने के कारण धूल उड़ती है और सांस लेना मुश्किल हो गया है।"),
    ("garbage", "कचरा पेटी पूरी तरह भरकर बह रही है और बदबू आ रही है।", "कचरा पेटी पूरी तरह भरकर बह रही है और बदबू आ रही है।"),
    ("garbage", "पिछले तीन दिनों से सफाई गाड़ी कचरा लेने नहीं आई है।", "पिछले तीन दिनों से सफाई गाड़ी कचरा लेने नहीं आई है।"),
    ("garbage", "कूड़े के ढेर पर आवारा मवेशी प्लास्टिक खा रहे हैं।", "कूड़े के ढेर पर आवारा मवेशी प्लास्टिक खा रहे हैं।"),
    ("garbage", "स्कूल के पास सड़ा हुआ कचरा पड़ा है जिससे बीमारी का खतरा है।", "स्कूल के पास सड़ा हुआ कचरा पड़ा है जिससे बीमारी का खतरा है।"),
    ("garbage", "सड़क पर लोग खुले में कचरा फेंक रहे हैं कोई रोक-टोक नहीं है।", "सड़क पर लोग खुले में कचरा फेंक रहे हैं कोई रोक-टोक नहीं है।"),
    ("garbage", "सब्जी मंडी में कचरे की नियमित सफाई नहीं की जा रही है।", "सब्जी मंडी में कचरे की नियमित सफाई नहीं की जा रही है।"),
    ("water_supply", "कालोनी में पिछले दो दिनों से पानी की सप्लाई पूरी तरह बंद है।", "कालोनी में पिछले दो दिनों से पानी की सप्लाई पूरी तरह बंद है।"),
    ("water_supply", "नल में बहुत गंदा और मटमैला पानी आ रहा है जो पीने योग्य नहीं है।", "नल में बहुत गंदा और मटमैला पानी आ रहा है जो पीने योग्य नहीं है।"),
    ("water_supply", "मुख्य पाइपलाइन फटने से सड़कों पर पीने का पानी बह रहा है।", "मुख्य पाइपलाइन फटने से सड़कों पर पीने का पानी बह रहा है।"),
    ("water_supply", "पानी का दबाव बहुत कम है जिससे ऊपरी मंजिल तक पानी नहीं चढ़ता।", "पानी का दबाव बहुत कम है जिससे ऊपरी मंजिल तक पानी नहीं चढ़ता।"),
    ("water_supply", "पानी आने का कोई निश्चित समय नहीं है कभी रात दो बजे आता है।", "पानी आने का कोई निश्चित समय नहीं है कभी रात दो बजे आता है।"),
    ("water_supply", "वाल्व खराब होने के कारण पानी नाले में बह रहा है।", "वाल्व खराब होने के कारण पानी नाले में बह रहा है।"),
    ("street_light", "मेन रोड की स्ट्रीट लाइट पिछले एक हफ्ते से खराब पड़ी है।", "मेन रोड की स्ट्रीट लाइट पिछले एक हफ्ते से खराब पड़ी है।"),
    ("street_light", "गली में अंधेरा होने की वजह से चोरी की घटनाएं बढ़ गई हैं।", "गली में अंधेरा होने की वजह से चोरी की घटनाएं बढ़ गई हैं।"),
    ("street_light", "बिजली का खंभा टेढ़ा हो गया है जो कभी भी गिर सकता है।", "बिजली का खंभा टेढ़ा हो गया है जो कभी भी गिर सकता है।"),
    ("street_light", "खंभे से नंगे तार लटक रहे हैं जिससे करंट लगने का खतरा है।", "खंभे से नंगे तार लटक रहे हैं जिससे करंट लगने का खतरा है।"),
    ("street_light", "दिन में भी लाइटें जलती रहती हैं और बिजली की बर्बादी होती है।", "दिन में भी लाइटें जलती रहती हैं और बिजली की बर्बादी होती है।"),
    ("street_light", "पेड़ों की टहनियों के कारण सड़क पर रोशनी नहीं आ पाती है।", "पेड़ों की टहनियों के कारण सड़क पर रोशनी नहीं आ पाती है।"),
    ("drainage", "खुला नाला ओवरफ्लो होकर गंदा पानी सड़क पर भर रहा है।", "खुला नाला ओवरफ्लो होकर गंदा पानी सड़क पर भर रहा है।"),
    ("drainage", "नाली में प्लास्टिक कचरा फंसा होने के कारण पानी रुका हुआ है।", "नाली में प्लास्टिक कचरा फंसा होने के कारण पानी रुका हुआ है।"),
    ("drainage", "सीवर का ढक्कन टूटा हुआ है जिसमें बच्चे गिर सकते हैं।", "सीवर का ढक्कन टूटा हुआ है जिसमें बच्चे गिर सकते हैं।"),
    ("drainage", "गंदे नाले की वजह से इलाके में मच्छरों का भारी आतंक है।", "गंदे नाले की वजह से इलाके में मच्छरों का भारी आतंक है।"),
    ("drainage", "बारिश के पानी की निकासी न होने से दुकानों में पानी भर गया है।", "बारिश के पानी की निकासी न होने से दुकानों में पानी भर गया है।"),
    ("drainage", "सफाई कर्मचारियों ने नाली से कीचड़ निकालकर सड़क पर ही छोड़ दिया।", "सफाई कर्मचारियों ने नाली से कीचड़ निकालकर सड़क पर ही छोड़ दिया।"),
    ("traffic", "चौराहे की ट्रैफिक लाइट बंद है जिससे भारी जाम लगा रहता है।", "चौराहे की ट्रैफिक लाइट बंद है जिससे भारी जाम लगा रहता है।"),
    ("traffic", "लेफ्ट टर्न पर गाड़ियां पार्क कर दी जाती हैं जिससे रास्ता रुक जाता है।", "लेफ्ट टर्न पर गाड़ियां पार्क कर दी जाती हैं जिससे रास्ता रुक जाता है।"),
    ("traffic", "बस स्टैंड के ठीक सामने ऑटो वाले खड़े होकर रास्ता रोकते हैं।", "बस स्टैंड के ठीक सामने ऑटो वाले खड़े होकर रास्ता रोकते हैं।"),
    ("traffic", "स्कूल के पास जेब्रा क्रॉसिंग न होने से बच्चों को सड़क पार करने में डर लगता है।", "स्कूल के पास जेब्रा क्रॉसिंग न होने से बच्चों को सड़क पार करने में डर लगता है।"),
    ("traffic", "ठेले वालों ने सड़क पर कब्जा कर रखा है जिससे पैदल चलना मुश्किल है।", "ठेले वालों ने सड़क पर कब्जा कर रखा है जिससे पैदल चलना मुश्किल है।"),
    ("traffic", "व्यस्त समय में ट्रैफिक पुलिस नदारद रहती है।", "व्यस्त समय में ट्रैफिक पुलिस नदारद रहती है।"),
    ("electricity", "दिन में दस बार बिजली कटती है जिससे इनवर्टर भी डिस्चार्ज हो गया।", "दिन में दस बार बिजली कटती है जिससे इनवर्टर भी डिस्चार्ज हो गया।"),
    ("electricity", "हाई वोल्टेज की वजह से घर के पंखे और फ्रिज खराब हो गए।", "हाई वोल्टेज की वजह से घर के पंखे और फ्रिज खराब हो गए।"),
    ("electricity", "बिजली की हाई टेंशन तार मकान की छत से बहुत पास गुजर रही है।", "बिजली की हाई टेंशन तार मकान की छत से बहुत पास गुजर रही है।"),
    ("electricity", "ट्रांसफार्मर में तेज चिंगारी निकल रही है और धुआं उठ रहा है।", "ट्रांसफार्मर में तेज चिंगारी निकल रही है और धुआं उठ रहा है।"),
    ("electricity", "डीपी बाक्स का दरवाजा खुला है और बच्चे वहां खेलते हैं।", "डीपी बाक्स का दरवाजा खुला है और बच्चे वहां खेलते हैं।"),
    ("electricity", "भूमिगत केबल जलने से पूरा मोहल्ला रातभर अंधेरे में रहा।", "भूमिगत केबल जलने से पूरा मोहल्ला रातभर अंधेरे में रहा।"),
    ("public_transport", "सरकारी बस अपने निर्धारित समय से एक घंटा देरी से आई।", "सरकारी बस अपने निर्धारित समय से एक घंटा देरी से आई।"),
    ("public_transport", "बस की सीटें टूटी हैं और फर्श पर लोहे के नुकीले टुकड़े निकले हैं।", "बस की सीटें टूटी हैं और फर्श पर लोहे के नुकीले टुकड़े निकले हैं।"),
    ("public_transport", "ड्राइवर ने बस को स्टॉप पर नहीं रोका और सीधे निकाल ले गया।", "ड्राइवर ने बस को स्टॉप पर नहीं रोका और सीधे निकाल ले गया।"),
    ("public_transport", "कंडक्टर ने टिकट के बाकी पैसे वापस नहीं किए और बदतमीजी की।", "कंडक्टर ने टिकट के बाकी पैसे वापस नहीं किए और बदतमीजी की।"),
    ("public_transport", "बस शेल्टर की छत टूटी है जिससे धूप और बारिश से बचाव नहीं होता।", "बस शेल्टर की छत टूटी है जिससे धूप और बारिश से बचाव नहीं होता।"),
    ("public_transport", "बस स्टैंड पर डिस्प्ले बोर्ड बंद पड़ा है समय का पता नहीं चलता।", "बस स्टैंड पर डिस्प्ले बोर्ड बंद पड़ा है समय का पता नहीं चलता।"),
    ("noise", "आधी रात को तेज आवाज में लाउडस्पीकर बजाया जा रहा है।", "आधी रात को तेज आवाज में लाउडस्पीकर बजाया जा रहा है।"),
    ("noise", "अस्पताल के बाहर ट्रक वाले तेज प्रेशर हॉर्न बजा रहे हैं।", "अस्पताल के बाहर ट्रक वाले तेज प्रेशर हॉर्न बजा रहे हैं।"),
    ("noise", "आवासीय क्षेत्र में अवैध फैक्ट्री की मशीनों से रातभर शोर होता है।", "आवासीय क्षेत्र में अवैध फैक्ट्री की मशीनों से रातभर शोर होता है।"),
    ("noise", "रात को दो बजे सीमेंट मिक्सर और ड्रिल मशीन चलाई जा रही है।", "रात को दो बजे सीमेंट मिक्सर और ड्रिल मशीन चलाई जा रही है।"),
    ("noise", "शादी की बारात में सड़क पर तेज पटाखे फोड़े जा रहे हैं।", "शादी की बारात में सड़क पर तेज पटाखे फोड़े जा रहे हैं।"),
    ("illegal_dumping", "नदी के किनारे रात में चुपके से मलबा और कचरा डाला जा रहा है।", "नदी के किनारे रात में चुपके से मलबा और कचरा डाला जा रहा है।"),
    ("illegal_dumping", "खाली प्लाट में अस्पतालों का खतरनाक मेडिकल वेस्ट फेंका गया है।", "खाली प्लाट में अस्पतालों का खतरनाक मेडिकल वेस्ट फेंका गया है।"),
    ("illegal_dumping", "ट्रैक्टर ट्राली वाले सड़क के किनारे ईंट और पत्थर गिराकर भाग जाते हैं।", "ट्रैक्टर ट्राली वाले सड़क के किनारे ईंट और पत्थर गिराकर भाग जाते हैं।"),
    ("illegal_dumping", "रसायनों से भरा गंदा पानी नाले में टैंकर से बहाया जा रहा है।", "रसायनों से भरा गंदा पानी नाले में टैंकर से बहाया जा रहा है।"),
    ("illegal_dumping", "पहाड़ी पर प्लास्टिक कारखाने का कचरा फेंका जा रहा है।", "पहाड़ी पर प्लास्टिक कारखाने का कचरा फेंका जा रहा है।"),
    ("illegal_dumping", "सड़क पर पुराने टायर जमा करके रखे गए हैं जिससे आग लग सकती है।", "सड़क पर पुराने टायर जमा करके रखे गए हैं जिससे आग लग सकती है।"),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 4A: CODE-MIXED MARATHI-ENGLISH (40)
# Mix of cases that use marker-set words (realistic) and cases that
# use Marathi words NOT in the implementation's MARATHI_ROMANIZED_MARKERS
# to avoid 100% data leakage.
# ──────────────────────────────────────────────────────────────────────
CODE_MIXED_MR_EN = [
    # Cases using marker-set words (realistic real-world code-mixing)
    ("roads", "Pune madhe road var khup motha pothole aahe please fix.", "Pune madhe road var khup motha pothole aahe please fix."),
    ("roads", "Karve road var heavy monsoon nantar deep crater zala aahe.", "Karve road var heavy monsoon nantar deep crater zala aahe."),
    ("roads", "Baner road var speed breaker var white paint markings nahiet.", "Baner road var speed breaker var white paint markings nahiet."),
    ("roads", "Sinhagad road var road work ardhavat sodla aahe stones flying everywhere.", "Sinhagad road var road work ardhavat sodla aahe stones flying everywhere."),
    ("roads", "Station baher rickshaw stand samor severe mud and pothole aahe.", "Station baher rickshaw stand samor severe mud and pothole aahe."),
    ("garbage", "Kothrud depot javal waste container overflow houn bad smell yete.", "Kothrud depot javal waste container overflow houn bad smell yete."),
    ("garbage", "Bavdhan area madhe last 3 days pasun garbage truck aala nahi.", "Bavdhan area madhe last 3 days pasun garbage truck aala nahi."),
    ("garbage", "Trash heap var stray animals plastic khat aahet very unhygienic.", "Trash heap var stray animals plastic khat aahet very unhygienic."),
    ("water_supply", "Aundh society madhe low pressure tap water supply aahe.", "Aundh society madhe low pressure tap water supply aahe."),
    ("water_supply", "Main supply pipe leakage mule thousands of liters water waste zala.", "Main supply pipe leakage mule thousands of liters water waste zala."),
    ("street_light", "Viman Nagar main road var street lights work karat nahiet.", "Viman Nagar main road var street lights work karat nahiet."),
    ("street_light", "Internal lane madhe complete darkness aahe very unsafe for women.", "Internal lane madhe complete darkness aahe very unsafe for women."),
    ("drainage", "Paud road var open gutter overflow houn black sewage road var aala.", "Paud road var open gutter overflow houn black sewage road var aala."),
    ("drainage", "Storm water drain plastic silt mule completely choked zala aahe.", "Storm water drain plastic silt mule completely choked zala aahe."),
    ("traffic", "Swargate junction cha traffic signal malfunction zala aahe.", "Swargate junction cha traffic signal malfunction zala aahe."),
    ("traffic", "Left turn var illegal parking mule bus block hot aahe.", "Left turn var illegal parking mule bus block hot aahe."),
    ("electricity", "Model Colony area madhe frequent power cuts hot aahet.", "Model Colony area madhe frequent power cuts hot aahet."),
    ("electricity", "High voltage surge mule refrigerator and TV burnt zale.", "High voltage surge mule refrigerator and TV burnt zale."),
    ("public_transport", "PMPML bus office rush time madhe one hour late aali.", "PMPML bus office rush time madhe one hour late aali."),
    ("noise", "Midnight nantar residential area madhe loud DJ music chalu aahe.", "Midnight nantar residential area madhe loud DJ music chalu aahe."),
    # Cases using Marathi words NOT in MARATHI_ROMANIZED_MARKERS (leak-free)
    # These use real Marathi words: dukaan, samasya, vinaanti, paisa, gaadi, takraar, sarkari, mohalla
    ("garbage", "Amchya mohalla madhye garbage collection band aahe last week pasun.", "Amchya mohalla madhye garbage collection band aahe last week pasun."),
    ("roads", "Aamchya galli madhe main road broken aahe gaadi driving mushkil.", "Aamchya galli madhe main road broken aahe gaadi driving mushkil."),
    ("water_supply", "Sarkari pipeline phutli aahe paani saglikade vahat aahe fix kara.", "Sarkari pipeline phutli aahe paani saglikade vahat aahe fix kara."),
    ("traffic", "Signal band aslyamule traffic jam hotoy vinaanti kara correct.", "Signal band aslyamule traffic jam hotoy vinaanti kara correct."),
    ("electricity", "Aamchya bhagat bijli nahi yete regularly please takraar ghya.", "Aamchya bhagat bijli nahi yete regularly please takraar ghya."),
    ("garbage", "Shejari dukaan wale rasta var kachra taktat daily complaint keli.", "Shejari dukaan wale rasta var kachra taktat daily complaint keli."),
    ("drainage", "Naala saaf kela nahi tar paavsat paani bhar-un yete basement madhe.", "Naala saaf kela nahi tar paavsat paani bhar-un yete basement madhe."),
    ("noise", "Raat bhar construction chalte aajubajuchya lokaana traas hotoy very disturbing.", "Raat bhar construction chalte aajubajuchya lokaana traas hotoy very disturbing."),
    ("public_transport", "Bus madhye itki gardi aste ki breathe karne pan mushkil very crowded.", "Bus madhye itki gardi aste ki breathe karne pan mushkil very crowded."),
    ("roads", "Footpath todun padli aahe ek senior citizen padla hospital neele ambulance.", "Footpath todun padli aahe ek senior citizen padla hospital neele ambulance."),
    # Additional realistic mixed cases
    ("water_supply", "Bore well cha paani contaminated aahe drinking safe nahi laboratory test kara.", "Bore well cha paani contaminated aahe drinking safe nahi laboratory test kara."),
    ("street_light", "Pole vr bulb nahi aahe ratri andhaar hoto women unsafe vaatate.", "Pole vr bulb nahi aahe ratri andhaar hoto women unsafe vaatate."),
    ("illegal_dumping", "Construction waste secretly dump kartaat raat-la riverbed var disgusting.", "Construction waste secretly dump kartaat raat-la riverbed var disgusting."),
    ("electricity", "Transformer blast zala sparks udat aahet fire risk aahe urgent attention.", "Transformer blast zala sparks udat aahet fire risk aahe urgent attention."),
    ("noise", "Pub chya loud music mule ratri zop yet nahi residents upset aahet.", "Pub chya loud music mule ratri zop yet nahi residents upset aahet."),
    ("drainage", "Gutter cha paani road var yet aahe mosquito breeding ground banlya.", "Gutter cha paani road var yet aahe mosquito breeding ground banlya."),
    ("traffic", "School samor zebra crossing nahi aahe students risking life daily.", "School samor zebra crossing nahi aahe students risking life daily."),
    ("garbage", "Dead animal padla aahe road var koni uthavat nahi stink unbearable.", "Dead animal padla aahe road var koni uthavat nahi stink unbearable."),
    ("roads", "Divider todla aahe concrete scattered var highway dangerous driving condition.", "Divider todla aahe concrete scattered var highway dangerous driving condition."),
    ("water_supply", "Tanker cha paani vikat ghyave lagte municipality supply band aahe.", "Tanker cha paani vikat ghyave lagte municipality supply band aahe."),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 4B: CODE-MIXED HINDI-ENGLISH (15) — new category
# ──────────────────────────────────────────────────────────────────────
CODE_MIXED_HI_EN = [
    ("roads", "Yahan road par bahut bada pothole hai please repair karo urgently.", "Yahan road par bahut bada pothole hai please repair karo urgently."),
    ("garbage", "Kuda ghar ke bahar waste pile ho gaya hai garbage truck nahi aata.", "Kuda ghar ke bahar waste pile ho gaya hai garbage truck nahi aata."),
    ("water_supply", "Paani supply do din se bilkul band hai please check pipeline.", "Paani supply do din se bilkul band hai please check pipeline."),
    ("street_light", "Street light kharab hai raat ko andhera hota hai danger hai.", "Street light kharab hai raat ko andhera hota hai danger hai."),
    ("drainage", "Naali ka paani overflow hokar sadak par aa raha hai drainage fix karo.", "Naali ka paani overflow hokar sadak par aa raha hai drainage fix karo."),
    ("traffic", "Traffic signal band hai subah se bahut bada jam lag raha hai.", "Traffic signal band hai subah se bahut bada jam lag raha hai."),
    ("electricity", "Bijli baar baar jaati hai daily power cut hota hai complaint karo.", "Bijli baar baar jaati hai daily power cut hota hai complaint karo."),
    ("noise", "Raat ko factory ka shor bahut hota hai neend nahi aati help karo.", "Raat ko factory ka shor bahut hota hai neend nahi aati help karo."),
    ("public_transport", "Bus time par nahi aati morning mein office late ho jaata hai.", "Bus time par nahi aati morning mein office late ho jaata hai."),
    ("illegal_dumping", "Nadi ke paas chemical waste dump ho raha hai secretly raat ko.", "Nadi ke paas chemical waste dump ho raha hai secretly raat ko."),
    ("roads", "Main road par pothole ki wajah se major accident ka risk hai.", "Main road par pothole ki wajah se major accident ka risk hai."),
    ("garbage", "Society ke main gate ke samne dustbin overflow ho gaya hai smelly waste.", "Society ke main gate ke samne dustbin overflow ho gaya hai smelly waste."),
    ("water_supply", "Pipeline leakage ki wajah se drinking water waste ho raha hai daily.", "Pipeline leakage ki wajah se drinking water waste ho raha hai daily."),
    ("electricity", "Voltage fluctuation ki wajah se AC and lights damage ho gayi hain.", "Voltage fluctuation ki wajah se AC and lights damage ho gayi hain."),
    ("street_light", "Crossroad par high mast light band padi hai dark area ban gaya.", "Crossroad par high mast light band padi hai dark area ban gaya."),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 4C: ROMANIZED HINDI, NO ENGLISH (8) — new category
# These contain Hindi words only in Latin script, no English words.
# ──────────────────────────────────────────────────────────────────────
ROMANIZED_HINDI = [
    ("roads", "Sadak par bahut bada gaddha hai gaadi fis rahi hai.", "Sadak par bahut bada gaddha hai gaadi fis rahi hai."),
    ("garbage", "Kachra gaadi teen din se nahi aayi hai bahut gandagi hai.", "Kachra gaadi teen din se nahi aayi hai bahut gandagi hai."),
    ("water_supply", "Paani do din se nahi aaya hai bahut mushkil ho raha hai.", "Paani do din se nahi aaya hai bahut mushkil ho raha hai."),
    ("drainage", "Naali band ho gayi hai gandha paani sadak par beh raha hai.", "Naali band ho gayi hai gandha paani sadak par beh raha hai."),
    ("electricity", "Bijli roz katti hai subah se shaam tak andhera rehta hai.", "Bijli roz katti hai subah se shaam tak andhera rehta hai."),
    ("noise", "Gaadiyon ka shor raat bhar rehta hai sone mein dikkat hoti hai.", "Gaadiyon ka shor raat bhar rehta hai sone mein dikkat hoti hai."),
    ("street_light", "Galli ke saare khambe band hain raat ko bahut andhera hota hai.", "Galli ke saare khambe band hain raat ko bahut andhera hota hai."),
    ("public_transport", "Bas samay par nahi aati ghanton khade rehna padta hai.", "Bas samay par nahi aati ghanton khade rehna padta hai."),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 4D: ROMANIZED MARATHI, NO ENGLISH (7) — explicit category
# ──────────────────────────────────────────────────────────────────────
ROMANIZED_MARATHI = [
    ("roads", "Rastyavar khup motha khadda padla aahe apghaatacha dhoka aahe.", "Rastyavar khup motha khadda padla aahe apghaatacha dhoka aahe."),
    ("garbage", "Ghanta gaadi aali nahi teen divsaanpasun kachra saathla aahe.", "Ghanta gaadi aali nahi teen divsaanpasun kachra saathla aahe."),
    ("water_supply", "Nalatun paani yet nahi don divsaanpasun khup traas hotoy.", "Nalatun paani yet nahi don divsaanpasun khup traas hotoy."),
    ("drainage", "Gutaraatun saandpaani vahat aahe rastyavar durgandhee yete.", "Gutaraatun saandpaani vahat aahe rastyavar durgandhee yete."),
    ("street_light", "Pathdeeve band aahet gallit andhaar aahe mahilaanna bhiti vaatate.", "Pathdeeve band aahet gallit andhaar aahe mahilaanna bhiti vaatate."),
    ("noise", "Raatri khup motthya aawazat gaani vajavli jaataat traas hoto.", "Raatri khup motthya aawazat gaani vajavli jaataat traas hoto."),
    ("traffic", "Chowk madhye vahatuk kondi zali aahe police konihi nahi.", "Chowk madhye vahatuk kondi zali aahe police konihi nahi."),
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 5: NORMALIZATION STRESS TESTS (30)
# These have INDEPENDENTLY DEFINED expected outputs based on the
# documented normalization rules in backend/app/services/normalization.py:
#   1. Unicode NFKC + invisible char stripping
#   2. Whitespace collapse (multi-space → single, 3+ newlines → 2)
#   3. Punctuation dedup (!! → !, ?? → ?, .... → ...)
#   4. Elongated char reduction (3+ identical → 1, or 2 for 'o')
# Expected outputs were derived by manually applying these rules.
# ──────────────────────────────────────────────────────────────────────
NORMALIZATION_STRESS_CASES = [
    # Whitespace cases
    {
        "original": "Road   var   khup   pothole   aahe",
        "expected_norm": "Road var khup pothole aahe",
        "norm_category": "whitespace",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "Garbage\t\tcollection\t\tnot\t\tdone",
        "expected_norm": "Garbage collection not done",
        "norm_category": "whitespace",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "  Water supply band aahe   ",
        "expected_norm": "Water supply band aahe",
        "norm_category": "whitespace",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "रस्त्यावर   खूप   मोठा   खड्डा   आहे",
        "expected_norm": "रस्त्यावर खूप मोठा खड्डा आहे",
        "norm_category": "whitespace",
        "language": "mr", "script": "devanagari", "is_code_mixed": False,
    },
    {
        "original": "सड़क   पर   बहुत   बड़ा   गड्ढा   है",
        "expected_norm": "सड़क पर बहुत बड़ा गड्ढा है",
        "norm_category": "whitespace",
        "language": "hi", "script": "devanagari", "is_code_mixed": False,
    },
    # Punctuation cases
    {
        "original": "Road is broken!!!!!!",
        "expected_norm": "Road is broken!",
        "norm_category": "punctuation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "Why is this not fixed?????",
        "expected_norm": "Why is this not fixed?",
        "norm_category": "punctuation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "No water supply........",
        "expected_norm": "No water supply...",
        "norm_category": "punctuation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "Fix the pothole!!!!!! Very dangerous!!!",
        "expected_norm": "Fix the pothole! Very dangerous!",
        "norm_category": "punctuation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "पाणी येत नाही!!!!!!",
        "expected_norm": "पाणी येत नाही!",
        "norm_category": "punctuation",
        "language": "mr", "script": "devanagari", "is_code_mixed": False,
    },
    # Elongated character cases
    {
        "original": "khupppp motha pothole aahe",
        "expected_norm": "khup motha pothole aahe",
        "norm_category": "elongation",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "potholessss on the road everywhere",
        "expected_norm": "potholes on the road everywhere",
        "norm_category": "elongation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "Roadddd is completely brokennnn",
        "expected_norm": "Road is completely broken",
        "norm_category": "elongation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "helpppp fix this issueee pleaseee",
        "expected_norm": "help fix this issue please",
        "norm_category": "elongation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "sooooo bad water quality goooood luck getting clean water",
        "expected_norm": "soo bad water quality good luck getting clean water",
        "norm_category": "elongation",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    # Unicode invisible character cases
    {
        "original": "Road\u200b var\u200b pothole\u200b aahe",
        "expected_norm": "Road var pothole aahe",
        "norm_category": "unicode",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "\ufeffGarbage collection not done properly",
        "expected_norm": "Garbage collection not done properly",
        "norm_category": "unicode",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "रस्ता\u200bवर खड्डा\u200b आहे",
        "expected_norm": "रस्तावर खड्डा आहे",
        "norm_category": "unicode",
        "language": "mr", "script": "devanagari", "is_code_mixed": False,
    },
    {
        "original": "\u202aStreet light\u202c band aahe",
        "expected_norm": "Street light band aahe",
        "norm_category": "unicode",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    # Combined noise cases
    {
        "original": "  Pune madhe   road var   potholessss   aahe!!!!!!  ",
        "expected_norm": "Pune madhe road var potholes aahe!",
        "norm_category": "combined",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "\u200bRoad\u200b   completely   brokennnn!!!!!!",
        "expected_norm": "Road completely broken!",
        "norm_category": "combined",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "  Water   supply   band   aahe??????   helpppp  ",
        "expected_norm": "Water supply band aahe? help",
        "norm_category": "combined",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "Garbage\t\tnot\t\tcollected........   veryyy bad smell",
        "expected_norm": "Garbage not collected... very bad smell",
        "norm_category": "combined",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "  रस्त्यावर   खूप   खड्डे   पडले!!!!!!  ",
        "expected_norm": "रस्त्यावर खूप खड्डे पडले!",
        "norm_category": "combined",
        "language": "mr", "script": "devanagari", "is_code_mixed": False,
    },
    {
        "original": "\ufeff  सड़क   पर   गड्ढा   है??????  ",
        "expected_norm": "सड़क पर गड्ढा है?",
        "norm_category": "combined",
        "language": "hi", "script": "devanagari", "is_code_mixed": False,
    },
    # ALL-CAPS cases (triggers needs_semantic_llm via assess_semantic_llm_need)
    {
        "original": "ROAD VAR KHUP MOTHA POTHOLE AAHE PLEASE FIX URGENTLY",
        "expected_norm": "ROAD VAR KHUP MOTHA POTHOLE AAHE PLEASE FIX URGENTLY",
        "norm_category": "allcaps",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "GARBAGE NOT COLLECTED SINCE LAST WEEK VERY BAD SMELL EVERYWHERE",
        "expected_norm": "GARBAGE NOT COLLECTED SINCE LAST WEEK VERY BAD SMELL EVERYWHERE",
        "norm_category": "allcaps",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    # ALL-CAPS + elongation combined (triggers needs_semantic_llm)
    {
        "original": "PUNE MADHE ROAD VAR KHUPPPPPP POTHOLE AAHE!!!!!!",
        "expected_norm": "PUNE MADHE ROAD VAR KHUP POTHOLE AAHE!",
        "norm_category": "allcaps_combined",
        "language": "mr-en", "script": "latin", "is_code_mixed": True,
    },
    {
        "original": "WATER SUPPLY COMPLETELY CUTTTTTT SINCE TWO DAYS??????",
        "expected_norm": "WATER SUPPLY COMPLETELY CUT SINCE TWO DAYS?",
        "norm_category": "allcaps_combined",
        "language": "en", "script": "latin", "is_code_mixed": False,
    },
    {
        "original": "\ufeffरस्त्यावर\u200b खूप खड्डे पडले आहेत",
        "expected_norm": "रस्त्यावर खूप खड्डे पडले आहेत",
        "norm_category": "unicode",
        "language": "mr", "script": "devanagari", "is_code_mixed": False,
    },
]

# ──────────────────────────────────────────────────────────────────────
# SECTION 6: EDGE CASES (20)
# Empty, short, ambiguous, mixed-script
# ──────────────────────────────────────────────────────────────────────
EDGE_CASES = [
    # Empty / whitespace-only
    {
        "original": "",
        "expected_lang": "unknown", "expected_script": "unknown",
        "is_code_mixed": False, "expected_norm": "",
        "edge_type": "empty", "label_source": "unambiguous",
    },
    {
        "original": "   ",
        "expected_lang": "unknown", "expected_script": "unknown",
        "is_code_mixed": False, "expected_norm": "",
        "edge_type": "whitespace_only", "label_source": "unambiguous",
    },
    {
        "original": "\t\n  \t",
        "expected_lang": "unknown", "expected_script": "unknown",
        "is_code_mixed": False, "expected_norm": "",
        "edge_type": "whitespace_only", "label_source": "unambiguous",
    },
    # Short inputs
    {
        "original": "Pothole",
        "expected_lang": "en", "expected_script": "latin",
        "is_code_mixed": False, "expected_norm": "Pothole",
        "edge_type": "short", "label_source": "curated",
    },
    {
        "original": "खड्डा",
        "expected_lang": "mr", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "खड्डा",
        "edge_type": "short", "label_source": "curated",
    },
    {
        "original": "गड्ढा",
        "expected_lang": "hi", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "गड्ढा",
        "edge_type": "short", "label_source": "review_needed",
        # Note: single Devanagari word — language ambiguous between hi/mr
    },
    {
        "original": "Fix road",
        "expected_lang": "en", "expected_script": "latin",
        "is_code_mixed": False, "expected_norm": "Fix road",
        "edge_type": "short", "label_source": "curated",
    },
    {
        "original": "पाणी नाही",
        "expected_lang": "mr", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "पाणी नाही",
        "edge_type": "short", "label_source": "curated",
        # "पाणी" is distinctly Marathi (Hindi uses "पानी")
    },
    # Mixed-script (Devanagari + Latin in same text)
    {
        "original": "FC Road वर खूप मोठा खड्डा आहे",
        "expected_lang": "mr-en", "expected_script": "mixed",
        "is_code_mixed": True, "expected_norm": "FC Road वर खूप मोठा खड्डा आहे",
        "edge_type": "mixed_script", "label_source": "curated",
    },
    {
        "original": "MG Road पर बहुत बड़ा गड्ढा है",
        "expected_lang": "hi-en", "expected_script": "mixed",
        "is_code_mixed": True, "expected_norm": "MG Road पर बहुत बड़ा गड्ढा है",
        "edge_type": "mixed_script", "label_source": "curated",
    },
    {
        "original": "PMPML बस वेळेवर येत नाही daily late",
        "expected_lang": "mr-en", "expected_script": "mixed",
        "is_code_mixed": True, "expected_norm": "PMPML बस वेळेवर येत नाही daily late",
        "edge_type": "mixed_script", "label_source": "curated",
    },
    {
        "original": "Aundh मधील society ला water supply कमी आहे",
        "expected_lang": "mr-en", "expected_script": "mixed",
        "is_code_mixed": True, "expected_norm": "Aundh मधील society ला water supply कमी आहे",
        "edge_type": "mixed_script", "label_source": "curated",
    },
    {
        "original": "Metro station के पास traffic bahut zyada hai",
        "expected_lang": "hi-en", "expected_script": "mixed",
        "is_code_mixed": True, "expected_norm": "Metro station के पास traffic bahut zyada hai",
        "edge_type": "mixed_script", "label_source": "curated",
    },
    # Ambiguous Hindi vs Marathi Devanagari
    {
        "original": "रस्ता खराब आहे दुरुस्ती करा.",
        "expected_lang": "mr", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "रस्ता खराब आहे दुरुस्ती करा.",
        "edge_type": "ambiguous_hi_mr", "label_source": "curated",
        # "आहे" and "करा" are distinctly Marathi
    },
    {
        "original": "पानी की समस्या बहुत गंभीर है।",
        "expected_lang": "hi", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "पानी की समस्या बहुत गंभीर है।",
        "edge_type": "ambiguous_hi_mr", "label_source": "curated",
        # "है", "की", "बहुत" are distinctly Hindi
    },
    {
        "original": "कृपया लवकर दुरुस्ती करावी.",
        "expected_lang": "mr", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "कृपया लवकर दुरुस्ती करावी.",
        "edge_type": "ambiguous_hi_mr", "label_source": "curated",
        # "करावी" is distinctly Marathi verbal form
    },
    {
        "original": "नगरपालिकेने तात्काळ कार्यवाही करावी.",
        "expected_lang": "mr", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "नगरपालिकेने तात्काळ कार्यवाही करावी.",
        "edge_type": "ambiguous_hi_mr", "label_source": "curated",
        # "नगरपालिकेने", "करावी" are distinctly Marathi
    },
    {
        "original": "नगरपालिका को तुरंत कार्रवाई करनी चाहिए।",
        "expected_lang": "hi", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "नगरपालिका को तुरंत कार्रवाई करनी चाहिए।",
        "edge_type": "ambiguous_hi_mr", "label_source": "curated",
        # "को", "करनी चाहिए" are distinctly Hindi
    },
    # Numeric-heavy
    {
        "original": "Ward 15, Plot 234, Lane 7 has drainage overflow since 3 days.",
        "expected_lang": "en", "expected_script": "latin",
        "is_code_mixed": False, "expected_norm": "Ward 15, Plot 234, Lane 7 has drainage overflow since 3 days.",
        "edge_type": "numeric_heavy", "label_source": "unambiguous",
    },
    {
        "original": "प्रभाग क्रमांक १२, रस्ता क्रमांक ४ येथे कचरा साचला आहे.",
        "expected_lang": "mr", "expected_script": "devanagari",
        "is_code_mixed": False, "expected_norm": "प्रभाग क्रमांक १२, रस्ता क्रमांक ४ येथे कचरा साचला आहे.",
        "edge_type": "numeric_heavy", "label_source": "unambiguous",
    },
]


def generate_dataset():
    dataset = []
    idx = 1

    # 1. English clean cases (60)
    for cat, text, norm in ENGLISH_COMPLAINTS[:60]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "english_clean",
            "original_text": text,
            "expected_language": "en",
            "expected_script": "latin",
            "is_code_mixed": False,
            "expected_normalized_text": norm,
            "label_source": "unambiguous",
        })
        idx += 1

    # 2. Marathi Devanagari clean cases (60)
    for cat, text, norm in MARATHI_COMPLAINTS[:60]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "marathi_devanagari_clean",
            "original_text": text,
            "expected_language": "mr",
            "expected_script": "devanagari",
            "is_code_mixed": False,
            "expected_normalized_text": norm,
            "label_source": "unambiguous",
        })
        idx += 1

    # 3. Hindi Devanagari clean cases (60)
    for cat, text, norm in HINDI_COMPLAINTS[:60]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "hindi_devanagari_clean",
            "original_text": text,
            "expected_language": "hi",
            "expected_script": "devanagari",
            "is_code_mixed": False,
            "expected_normalized_text": norm,
            "label_source": "unambiguous",
        })
        idx += 1

    # 4a. Code-mixed Marathi-English (40)
    for cat, text, norm in CODE_MIXED_MR_EN[:40]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "code_mixed_mr_en",
            "original_text": text,
            "expected_language": "mr-en",
            "expected_script": "latin",
            "is_code_mixed": True,
            "expected_normalized_text": norm,
            "label_source": "curated",
        })
        idx += 1

    # 4b. Code-mixed Hindi-English (15)
    for cat, text, norm in CODE_MIXED_HI_EN[:15]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "code_mixed_hi_en",
            "original_text": text,
            "expected_language": "hi-en",
            "expected_script": "latin",
            "is_code_mixed": True,
            "expected_normalized_text": norm,
            "label_source": "curated",
        })
        idx += 1

    # 4c. Romanized Hindi (8)
    for cat, text, norm in ROMANIZED_HINDI[:8]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "romanized_hindi",
            "original_text": text,
            "expected_language": "hi",
            "expected_script": "latin",
            "is_code_mixed": False,
            "expected_normalized_text": norm,
            "label_source": "curated",
        })
        idx += 1

    # 4d. Romanized Marathi (7)
    for cat, text, norm in ROMANIZED_MARATHI[:7]:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": cat,
            "eval_group": "romanized_marathi",
            "original_text": text,
            "expected_language": "mr",
            "expected_script": "latin",
            "is_code_mixed": False,
            "expected_normalized_text": norm,
            "label_source": "curated",
        })
        idx += 1

    # 5. Normalization stress tests
    for item in NORMALIZATION_STRESS_CASES:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": "normalization_stress",
            "eval_group": f"norm_stress_{item['norm_category']}",
            "original_text": item["original"],
            "expected_language": item["language"],
            "expected_script": item["script"],
            "is_code_mixed": item["is_code_mixed"],
            "expected_normalized_text": item["expected_norm"],
            "label_source": "curated",
        })
        idx += 1

    # 6. Edge cases
    for item in EDGE_CASES:
        dataset.append({
            "id": f"EVAL-{idx:04d}",
            "category": item.get("edge_type", "edge_case"),
            "eval_group": f"edge_{item['edge_type']}",
            "original_text": item["original"],
            "expected_language": item["expected_lang"],
            "expected_script": item["expected_script"],
            "is_code_mixed": item["is_code_mixed"],
            "expected_normalized_text": item["expected_norm"],
            "label_source": item["label_source"],
        })
        idx += 1

    DEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEST_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    # Print composition summary
    from collections import Counter
    groups = Counter(item["eval_group"] for item in dataset)
    sources = Counter(item["label_source"] for item in dataset)
    print(f"Successfully generated {len(dataset)} evaluation cases in {DEST_PATH}")
    print(f"\nComposition by eval_group:")
    for g, c in sorted(groups.items()):
        print(f"  {g}: {c}")
    print(f"\nLabel provenance:")
    for s, c in sorted(sources.items()):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    generate_dataset()
