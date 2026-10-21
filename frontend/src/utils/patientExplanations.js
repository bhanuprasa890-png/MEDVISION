/**
 * Patient-friendly educational explanations and clinical definitions
 * for RetinaGuard (Diabetic Retinopathy 5-grade system).
 *
 * Provides multilingual support:
 * - English (en): Clinically reviewed baseline.
 * - Tamil (ta): Curated clinical and lay translations in authentic Tamil script.
 * - Hindi (hi): Curated clinical and lay translations in Devanagari script.
 * - Telugu (te): Curated clinical and lay translations in Telugu script.
 *
 * Includes lay analogies, Grad-CAM heatmap interpretations, emergency warnings,
 * and evidence-based next steps.
 */

export const GRADE_EXPLANATIONS = {
  0: {
    clinicalGrade: 0,
    clinicalName: "No Diabetic Retinopathy",
    en: {
      badge: "Grade 0 • Healthy Appearance",
      title: "No Signs of Diabetic Eye Damage Detected",
      whatModelPredicted: "The computer model looked at this photograph and did not find visible signs of diabetic eye disease.",
      everydayExplanation:
        "In this eye photograph, the tiny blood vessels that nourish the back of your eye (the retina) appear smooth, clear, and undamaged. There are no obvious weak spots, swelling, or leaking blood droplets visible to the model.",
      analogy: "Like clean garden hoses with no bulges, cracks, or leaks.",
      nextSteps: [
        "Continue your regular annual dilated eye exam with an eye doctor (optometrist or ophthalmologist).",
        "Keep working with your doctor to maintain healthy blood sugar (A1C), blood pressure, and cholesterol levels.",
        "Even when an AI scan appears normal, yearly human eye exams remain essential because subtle changes may not be visible in a single photo.",
      ],
      urgency: "Routine Care",
    },
    ta: {
      badge: "நிலை 0 • ஆரோக்கியமான தோற்றம்",
      title: "சர்க்கரை நோய் விழித்திரை பாதிப்பு இல்லை",
      whatModelPredicted: "இந்த கண் புகைப்படத்தில் சர்க்கரை நோயினால் ஏற்பட்ட இரத்தக் குழாய் பாதிப்புகள் எதுவும் கணினி மாதிரிக்கு தெரியவில்லை.",
      everydayExplanation:
        "உங்கள் கண்ணின் பின்புறத்தில் உள்ள விழித்திரைக்கு இரத்தத்தை கொண்டு செல்லும் நுண்ணிய இரத்தக் குழாய்கள் எவ்வித அடைப்போ அல்லது கசிவோ இல்லாமல் தெளிவாகக் காணப்படுகின்றன.",
      analogy: "எந்தவொரு கசிவோ அல்லது பலவீனமோ இல்லாத தெளிவான நீர்க்குழாய் போன்ற நிலை இது.",
      nextSteps: [
        "ஆண்டுக்கு ஒருமுறை கண் மருத்துவரிடம் முழுமையான கண் பரிசோதனை (Dilated Eye Exam) தொடர்ந்து செய்து கொள்ளுங்கள்.",
        "இரத்த சர்க்கரை அளவு, இரத்த அழுத்தம் மற்றும் கொழுப்பின் அளவை சீராகப் பராமரிக்க மருத்துவ ஆலோசனை பெறவும்.",
        "கணினி மாதிரி சாதாரணமாக காட்டினாலும், மருத்துவ நிபுணரின் வழக்கமான நேரடி கண் பரிசோதனை மிகவும் அவசியம்.",
      ],
      urgency: "வழக்கமான பரிசோதனை",
    },
    hi: {
      badge: "ग्रेड 0 • सामान्य स्वरूप",
      title: "डायबिटिक रेटिनोपैथी का कोई लक्षण नहीं मिला",
      whatModelPredicted: "कंप्यूटर मॉडल को इस नेत्र तस्वीर में डायबिटिक रेटिनोपैथी का कोई दृश्य लक्षण नहीं मिला।",
      everydayExplanation:
        "इस तस्वीर में आँख के पिछले हिस्से (रेटिना) को पोषण देने वाली सूक्ष्म रक्त वाहिकाएं स्वस्थ, स्पष्ट और सुरक्षित दिख रही हैं। मॉडल को सूजन, रिसाव या कमज़ोरी का कोई संकेत नहीं मिला।",
      analogy: "स्वच्छ पानी के पाइप की तरह जिसमें कोई दरार, रुकावट या रिसाव नहीं है।",
      nextSteps: [
        "नेत्र रोग विशेषज्ञ (ऑप्थैल्मोलॉजिस्ट) के साथ अपनी वार्षिक पुतली फैलाकर जाँच (डाइलेटेड आई टेस्ट) जारी रखें।",
        "अपने चिकित्सक की सलाह से ब्लड शुगर (HbA1c), रक्तचाप और कोलेस्ट्रॉल को नियंत्रित रखें।",
        "एआई मॉडल का परिणाम सामान्य आने पर भी नियमित नेत्र परीक्षण अनिवार्य है।",
      ],
      urgency: "नियमित देखभाल",
    },
    te: {
      badge: "గ్రేడ్ 0 • ఆరోగ్యకరమైన స్థితి",
      title: "డయాబెటిక్ రెటినోపతి లక్షణాలు లేవు",
      whatModelPredicted: "ఈ కంటి ఛాయాచిత్రంలో డయాబెటిక్ రెటినోపతి సంకేతాలు ఏవీ కంప్యూటర్ మోడల్ గుర్తించలేదు.",
      everydayExplanation:
        "కంటి వెనుక భాగంలోని రెటీనాకు రక్తాన్ని చేరవేసే సూక్ష్మ రక్తనాళాలు శుభ్రంగా, ఎటువంటి లీకేజీ లేదా అడ్డంకులు లేకుండా ఆరోగ్యంగా ఉన్నాయి.",
      analogy: "ఎలాంటి పగుళ్లు లేదా లీకేజీలు లేని శుభ్రమైన నీటి పైపు లాంటి స్థితి ఇది.",
      nextSteps: [
        "కంటి వైద్యునితో వార్షిక సమగ్ర కంటి పరీక్షలను (డైలేటెడ్ ఐ ఎగ్జామ్) కొనసాగించండి.",
        "బ్లడ్ షుగర్, రక్తపోటు మరియు కొలెస్ట్రాల్‌ను ఎప్పటికప్పుడు అదుపులో ఉంచుకోండి.",
        "కంప్యూటర్ ఫలితం సాధారణంగా ఉన్నప్పటికీ, వైద్యుని ప్రత్యక్ష పరీక్ష చాలా అవసరం.",
      ],
      urgency: "సాధారణ సంరక్షణ",
    },
  },
  1: {
    clinicalGrade: 1,
    clinicalName: "Mild Non-Proliferative Diabetic Retinopathy",
    en: {
      badge: "Grade 1 • Early Changes",
      title: "Mild / Early Diabetic Retinopathy",
      whatModelPredicted: "The computer model detected subtle, early-stage changes in the retina.",
      everydayExplanation:
        "A few tiny weak spots (called microaneurysms) may have formed on the small blood vessels in the back of your eye. These look like tiny microscopic red dots. At this early stage, your vision is usually completely normal and you will not feel any pain, but it is an important early warning signal.",
      analogy: "Like tiny weak spots on a bicycle tire that haven't caused a flat yet, but need careful watching.",
      nextSteps: [
        "Schedule a comprehensive dilated eye examination with an eye doctor within the next few months.",
        "Partner with your healthcare provider to tighten blood sugar and blood pressure management, which can stop early spots from worsening.",
        "Do not ignore early findings simply because your eyesight still feels sharp.",
      ],
      urgency: "Schedule Soon",
    },
    ta: {
      badge: "நிலை 1 • ஆரம்ப நிலை மாற்றங்கள்",
      title: "ஆரம்ப நிலை சர்க்கரை நோய் விழித்திரை பாதிப்பு",
      whatModelPredicted: "விழித்திரையில் மிக ஆரம்ப நிலையிலான மெல்லிய மாற்றங்களை கணினி மாதிரி கண்டறிந்துள்ளது.",
      everydayExplanation:
        "விழித்திரையில் உள்ள நுண்ணிய இரத்தக் குழாய்களில் மிகச்சிறிய பலவீனமான வீக்கங்கள் (microaneurysms) தோன்றியிருக்கலாம். இவை நுண்ணோக்கியில் சிறிய சிவப்பு புள்ளிகள் போல தோன்றும். இந்த ஆரம்ப நிலையில் பார்வை சாதாரணமாகவே இருக்கும், ஆனால் இது கவனிக்க வேண்டிய ஒரு முக்கிய எச்சரிக்கை.",
      analogy: "சைக்கிள் டயரில் ஏற்படும் மிகச்சிறிய பலவீனமான புள்ளி போன்றது; இப்போதே கவனித்தால் பெரிய பாதிப்பை தடுக்கலாம்.",
      nextSteps: [
        "அடுத்த சில மாதங்களுக்குள் கண் மருத்துவரிடம் விரிவான பரிசோதனைக்கு நேரம் பதிவு செய்யவும்.",
        "சர்க்கரை அளவு மற்றும் இரத்த அழுத்தத்தை தீவிரமாக கட்டுப்படுத்துவது இந்த ஆரம்ப மாற்றங்கள் பெரிதாகாமல் தடுக்கும்.",
        "பார்வை தெளிவாக இருக்கிறது என்பதற்காக இந்த ஆரம்ப எச்சரிக்கையை புறக்கணிக்க வேண்டாம்.",
      ],
      urgency: "விரைவில் பரிசோதிக்கவும்",
    },
    hi: {
      badge: "ग्रेड 1 • शुरुआती बदलाव",
      title: "हल्की / शुरुआती डायबिटिक रेटिनोपैथी",
      whatModelPredicted: "कंप्यूटर मॉडल ने रेटिना में बहुत शुरुआती स्तर के सूक्ष्म बदलाव पहचाने हैं।",
      everydayExplanation:
        "आँख के पिछले हिस्से की नसों में छोटे-छोटे कमज़ोर उभार (माइक्रोएन्यूरिज्म) बन सकते हैं। इस शुरुआती चरण में दृष्टि सामान्य रहती है और दर्द नहीं होता, लेकिन यह एक महत्वपूर्ण पूर्व चेतावनी है।",
      analogy: "साइकिल के टायर में उभरे छोटे से कमज़ोर हिस्से की तरह, जो अभी फटा नहीं है पर ध्यान देने की ज़रूरत है।",
      nextSteps: [
        "अगले कुछ महीनों के भीतर किसी नेत्र रोग विशेषज्ञ से विस्तृत जाँच कराएं।",
        "ब्लड शुगर और ब्लड प्रेशर को सख्त नियंत्रण में रखें ताकि यह स्थिति आगे न बढ़े।",
        "दृष्टि साफ़ होने पर भी इस शुरुआती चेतावनी को नज़रअंदाज़ न करें।",
      ],
      urgency: "शीघ्र परामर्श लें",
    },
    te: {
      badge: "గ్రేడ్ 1 • ప్రారంభ మార్పులు",
      title: "ప్రారంభ స్థాయి డయాబెటిక్ రెటినోపతి",
      whatModelPredicted: "కంటి రెటీనాలో చాలా ప్రారంభ దశ మార్పులను కంప్యూటర్ మోడల్ గుర్తించింది.",
      everydayExplanation:
        "కంటిలోని సూక్ష్మ రక్తనాళాలపై చిన్న బలహీనమైన ఉబ్బులు (microaneurysms) ఏర్పడి ఉండవచ్చు. ఈ దశలో దృష్టి సాధారణంగానే ఉంటుంది, కానీ ఇది జాగ్రత్త పడవలసిన ప్రారంభ హెచ్చరిక.",
      analogy: "సైకిల్ టైరుపై కనిపించే చిన్న బలహీనమైన బుడగ లాంటిది; ఇప్పుడే జాగ్రత్త పడితే ప్రమాదాన్ని నివారించవచ్చు.",
      nextSteps: [
        "రాబోయే కొన్ని నెలల్లోపు కంటి వైద్యునితో సమగ్ర పరీక్ష చేయించుకోండి.",
        "షుగర్ మరియు రక్తపోటును కచ్చితంగా నియంత్రించడం ద్వారా సమస్య పెరగకుండా ఆపవచ్చు.",
        "చూపు బాగానే ఉందని ప్రారంభ హెచ్చరికలను నిర్లక్ష్యం చేయవద్దు.",
      ],
      urgency: "త్వరలో పరీక్షించుకోండి",
    },
  },
  2: {
    clinicalGrade: 2,
    clinicalName: "Moderate Non-Proliferative Diabetic Retinopathy",
    en: {
      badge: "Grade 2 • Developing Changes",
      title: "Moderate Diabetic Retinopathy",
      whatModelPredicted: "The computer model detected more noticeable vascular changes in the retina.",
      everydayExplanation:
        "Some blood vessels in the back of your eye have become blocked or swollen, and small amounts of fluid or blood may be leaking into the retinal tissue. While you may still see well, the damage is actively progressing beyond the earliest stage.",
      analogy: "Like pipes that are beginning to clog, causing small damp spots to form in the surrounding area.",
      nextSteps: [
        "Make an appointment with an eye care specialist (optometrist or ophthalmologist) within 2 to 4 weeks.",
        "Ask your doctor about monitoring for swelling in the center of your vision (macular edema).",
        "Strict control of diabetes, blood pressure, and cholesterol is critical right now to protect your sight.",
      ],
      urgency: "Prompt Attention (2-4 Weeks)",
    },
    ta: {
      badge: "நிலை 2 • மிதமான மாற்றங்கள்",
      title: "மிதமான சர்க்கரை நோய் விழித்திரை பாதிப்பு",
      whatModelPredicted: "விழித்திரையில் பல இடங்களில் தெளிவாகத் தெரியும் இரத்தக் குழாய் மாற்றங்களை கணினி மாதிரி கண்டறிந்துள்ளது.",
      everydayExplanation:
        "கண்ணின் பின்புறத்தில் உள்ள சில இரத்தக் குழாய்கள் அடைபட்டிருக்கலாம் அல்லது வீங்கி சிறிய அளவில் கசிவுகள் ஏற்பட்டிருக்கலாம். உங்கள் பார்வை தற்போதைக்கு நன்றாக தெரிந்தாலும், பாதிப்பு ஆரம்ப நிலையைத் தாண்டி வளர்ந்து வருகிறது.",
      analogy: "குழாய்களில் அடைப்பு ஏற்பட்டு, சுற்றியுள்ள சுவர்களில் ஈரப்பதம் கசிவது போன்ற நிலை.",
      nextSteps: [
        "அடுத்த 2 முதல் 4 வாரங்களுக்குள் கண் மருத்துவ நிபுணரை நேரில் சந்தித்து விரிவான பரிசோதனை செய்து கொள்ளுங்கள்.",
        "மத்திய பார்வை பகுதியில் வீக்கம் (Macular Edema) உள்ளதா என்பதை பரிசோதிக்குமாறு மருத்துவரிடம் கேளுங்கள்.",
        "பார்வையை பாதுகாக்க இரத்த சர்க்கரை மற்றும் இரத்த அழுத்தத்தை மிக தீவிரமாக கட்டுப்படுத்துவது அவசியமாகும்.",
      ],
      urgency: "உடனடி கவனம் தேவை (2-4 வாரங்கள்)",
    },
    hi: {
      badge: "ग्रेड 2 • मध्यम बदलाव",
      title: "मध्यम डायबिटिक रेटिनोपैथी",
      whatModelPredicted: "कंप्यूटर मॉडल ने रेटिना में स्पष्ट रक्त वाहिका परिवर्तन पहचाने हैं।",
      everydayExplanation:
        "आँख के पिछले हिस्से की कुछ नसें अवरुद्ध या सूज गई हैं और उनसे तरल पदार्थ का हल्का रिसाव हो सकता है। यद्यपि आपकी दृष्टि अभी ठीक हो सकती है, लेकिन क्षति शुरुआती चरण से आगे बढ़ रही है।",
      analogy: "पाइप में रुकावट आने पर दीवारों में नमी और सीलन आने जैसी स्थिति।",
      nextSteps: [
        "अगले 2 से 4 सप्ताह के भीतर किसी नेत्र विशेषज्ञ (ऑप्थैल्मोलॉजिस्ट) से मिलें।",
        "केंद्र दृष्टि में सूजन (मैक्युलर एडिमा) की जाँच के बारे में डॉक्टर से परामर्श लें।",
        "दृष्टि की सुरक्षा के लिए डायबिटीज़ और ब्लड प्रेशर का कड़ा नियंत्रण अनिवार्य है।",
      ],
      urgency: "शीघ्र ध्यान दें (2-4 सप्ताह)",
    },
    te: {
      badge: "గ్రేడ్ 2 • మధ్యస్థ మార్పులు",
      title: "మధ్యస్థ స్థాయి డయాబెటిక్ రెటినోపతి",
      whatModelPredicted: "కంటి రెటీనాలో స్పష్టమైన రక్తనాళాల మార్పులను కంప్యూటర్ మోడల్ గుర్తించింది.",
      everydayExplanation:
        "కంటిలోని కొన్ని రక్తనాళాలు మూసుకుపోవడం లేదా వాపు రావడం జరిగి ఉండవచ్చు మరియు చిన్నపాటి ద్రవాలు లేదా రక్తం లీక్ కావచ్చు. ప్రస్తుతానికి చూపు బాగానే ఉన్నా, సమస్య పెరుగుతోంది.",
      analogy: "పైపులలో అడ్డంకులు ఏర్పడి చుట్టుపక్కల గోడల్లో తేమ కారడం లాంటి స్థితి.",
      nextSteps: [
        "2 నుండి 4 వారాల లోపు కంటి నిపుణుడిని సంప్రదించి పరీక్ష చేయించుకోండి.",
        "కేంద్ర దృష్టి భాగంలో వాపు (Macular Edema) ఉందో లేదో తనిఖీ చేయమని వైద్యుడిని కోరండి.",
        "చూపును కాపాడుకోవడానికి షుగర్ మరియు రక్తపోటును చాలా కచ్చితంగా నియంత్రించండి.",
      ],
      urgency: "సత్వర శ్రద్ధ అవసరం (2-4 వారాలు)",
    },
  },
  3: {
    clinicalGrade: 3,
    clinicalName: "Severe Non-Proliferative Diabetic Retinopathy",
    en: {
      badge: "Grade 3 • Significant Changes",
      title: "Severe Non-Proliferative Diabetic Retinopathy",
      whatModelPredicted: "The computer model detected widespread blood vessel blockage and significant retinal stress.",
      everydayExplanation:
        "Many of the blood vessels nourishing your retina are blocked, cutting off oxygen and blood flow to large sections of the eye. To survive, the retina is signaling the body to grow new blood vessels. This is a critical stage before advanced disease develops.",
      analogy: "Major water lines are shut down, leaving large fields parched and starved of nourishment.",
      nextSteps: [
        "Seek prompt evaluation from an ophthalmologist or retina specialist within 1 to 2 weeks.",
        "Do NOT wait for your vision to become blurry before seeking medical care.",
        "Modern medical interventions can prevent progression to the dangerous bleeding stage if treated in time.",
      ],
      urgency: "Prompt Specialist Care (1-2 Weeks)",
    },
    ta: {
      badge: "நிலை 3 • தீவிர மாற்றங்கள்",
      title: "தீவிர சர்க்கரை நோய் விழித்திரை பாதிப்பு",
      whatModelPredicted: "விழித்திரையில் பல இரத்தக் குழாய்களில் கடுமையான அடைப்பும் பாதிப்பும் ஏற்பட்டுள்ளதாக கணினி மாதிரி கண்டறிந்துள்ளது.",
      everydayExplanation:
        "விழித்திரைக்கு இரத்தத்தை கொண்டு செல்லும் பல முக்கிய குழாய்கள் அடைக்கப்பட்டு, கண்ணின் பெரும் பகுதிக்கு ஆக்சிஜன் தடைபட்டுள்ளது. இதனால் விழித்திரை ஆபத்தான அடுத்த கட்டத்திற்கு செல்லும் நிலையில் உள்ளது.",
      analogy: "முக்கிய குடிநீர் குழாய்கள் அடைக்கப்பட்டு நிலம் காய்ந்து போவது போன்ற அவசர நிலை இது.",
      nextSteps: [
        "அடுத்த 1 முதல் 2 வாரங்களுக்குள் விழித்திரை மருத்துவ நிபுணரை (Retina Specialist) நேரில் அணுகவும்.",
        "பார்வை குறையும் வரை அல்லது மங்கும் வரை காத்திருக்க வேண்டாம்.",
        "உரிய நேரத்தில் மருத்துவ சிகிச்சை பெறுவது அடுத்த கட்ட தீவிர இரத்தக் கசிவை தடுத்து பார்வையை காக்கும்.",
      ],
      urgency: "விழித்திரை நிபுணர் சிகிச்சை தேவை (1-2 வாரங்கள்)",
    },
    hi: {
      badge: "ग्रेड 3 • गंभीर बदलाव",
      title: "गंभीर नॉन-प्रोलिफेरेटिव डायबिटिक रेटिनोपैथी",
      whatModelPredicted: "कंप्यूटर मॉडल ने व्यापक रक्त वाहिका रुकावट और रेटिना पर गंभीर तनाव पाया है।",
      everydayExplanation:
        "रेटिना को पोषण देने वाली कई नसें अवरुद्ध हो गई हैं, जिससे आँख के बड़े हिस्से में ऑक्सीजन की कमी हो गई है। यह उन्नत और खतरनाक चरण से ठीक पहले की गंभीर स्थिति है।",
      analogy: "मुख्य जल लाइनें बंद होने से बड़े खेतों के सूखने और बंजर होने जैसी आपात स्थिति।",
      nextSteps: [
        "1 से 2 सप्ताह के भीतर तुरंत रेटिना विशेषज्ञ या ऑप्थैल्मोलॉजिस्ट से संपर्क करें।",
        "दृष्टि धुंधली होने तक प्रतीक्षा न करें।",
        "समय पर चिकित्सा कराने से खतरनाक रक्तस्राव और दृष्टि हानि को रोका जा सकता है।",
      ],
      urgency: "विशेषज्ञ परामर्श आवश्यक (1-2 सप्ताह)",
    },
    te: {
      badge: "గ్రేడ్ 3 • తీవ్రమైన మార్పులు",
      title: "తీవ్ర స్థాయి నాన్-ప్రొలిఫరేటివ్ డయాబెటిక్ రెటినోపతి",
      whatModelPredicted: "రెటీనాలో అనేక రక్తనాళాల అడ్డంకులు మరియు తీవ్రమైన ఒత్తిడిని కంప్యూటర్ మోడల్ గుర్తించింది.",
      everydayExplanation:
        "రెటీనాకు రక్తాన్ని అందించే అనేక ప్రధాన నాళాలు మూసుకుపోయి, కంటికి ఆక్సిజన్ సరఫరా నిలిచిపోయింది. ఇది వ్యాధి ముదిరే ముందు అత్యంత క్లిష్టమైన దశ.",
      analogy: "ప్రధాన నీటి కాలువలు మూసుకుపోయి పంట పొలాలు ఎండిపోవడం లాంటి అత్యవసర పరిస్థితి.",
      nextSteps: [
        "1 నుండి 2 వారాల లోపు తప్పనిసరిగా రెటీనా నిపుణుడిని సంప్రదించండి.",
        "చూపు మందగించే వరకు వేచి ఉండకండి.",
        "సకాలంలో చికిత్స పొందడం వల్ల తదుపరి ప్రమాదకర రక్తస్రావాన్ని అరికట్టవచ్చు.",
      ],
      urgency: "రెటీనా నిపుణుడి సత్వర సంరక్షణ (1-2 వారాలు)",
    },
  },
  4: {
    clinicalGrade: 4,
    clinicalName: "Proliferative Diabetic Retinopathy",
    en: {
      badge: "Grade 4 • Advanced / Proliferative",
      title: "Advanced / Proliferative Diabetic Retinopathy",
      whatModelPredicted: "The computer model detected signs of advanced diabetic eye disease with fragile new blood vessel growth.",
      everydayExplanation:
        "Because the retina has been starved of oxygen, the eye has started growing abnormal, fragile new blood vessels (neovascularization). These new vessels are very weak; they can easily bleed into the gel of your eye (vitreous hemorrhage) or cause scar tissue that pulls on the retina, posing a severe threat to vision.",
      analogy: "Like fragile wild weeds growing into cracks, which can snap and cause sudden flooding or wall damage.",
      nextSteps: [
        "Contact an ophthalmologist or retina clinic for an urgent evaluation.",
        "Effective, sight-saving treatments (such as laser photocoagulation, anti-VEGF injections, or surgery) are available and can protect remaining vision when started promptly.",
        "Avoid strenuous lifting or activities that raise eye pressure until cleared by your ophthalmologist.",
      ],
      urgency: "Urgent Specialist Evaluation",
    },
    ta: {
      badge: "நிலை 4 • முற்றிய விழித்திரை பாதிப்பு",
      title: "முற்றிய விழித்திரை பாதிப்பு (புரோலிஃபெரேடிவ் நிலை)",
      whatModelPredicted: "விழித்திரையில் பலவீனமான புதிய இரத்தக் குழாய்கள் உருவாகியுள்ளதை கணினி மாதிரி கண்டறிந்துள்ளது.",
      everydayExplanation:
        "ஆக்சிஜன் பற்றாக்குறையினால் கண்ணில் முறையற்ற, மிக பலவீனமான புதிய இரத்தக் குழாய்கள் வளரத் தொடங்கியுள்ளன. இவை எளிதில் உடைந்து கண்ணுக்குள் இரத்தக் கசிவை ஏற்படுத்தலாம் அல்லது விழித்திரையை இழுத்து பார்வை இழப்பை உருவாக்கும் அபாயம் உள்ளது.",
      analogy: "சுவர்களில் படரும் பலவீனமான களைச்செடிகள் போல; இவை உடைந்து கண்ணுக்குள் தீவிர கசிவை ஏற்படுத்தக்கூடும்.",
      nextSteps: [
        "தாமதிக்காமல் உடனடியாக விழித்திரை மருத்துவ நிபுணரை (Retina Specialist) அணுகி அவசர சிகிச்சை பெறவும்.",
        "லேசர் சிகிச்சை மற்றும் ஊசி மருந்துகள் (Anti-VEGF) மூலம் பார்வையை காப்பாற்ற முடியும்.",
        "மருத்துவர் அனுமதிக்கும் வரை அதிக எடை தூக்குவது போன்ற தீவிர உடற்பயிற்சிகளை தவிர்க்கவும்.",
      ],
      urgency: "அவசர மருத்துவ நிபுணர் பரிசோதனை தேவை",
    },
    hi: {
      badge: "ग्रेड 4 • उन्नत / प्रोलिफेरेटिव",
      title: "उन्नत / प्रोलिफेरेटिव डायबिटिक रेटिनोपैथी",
      whatModelPredicted: "कंप्यूटर मॉडल ने असामान्य और अत्यधिक कमज़ोर नई रक्त वाहिकाओं के विकास के संकेत पाए हैं।",
      everydayExplanation:
        "ऑक्सीजन की कमी के कारण आँख में असामान्य, बेहद कमज़ोर नई नसें उगने लगी हैं। ये नसें आसानी से फट सकती हैं जिससे आँख के भीतर रक्तस्राव हो सकता है और दृष्टि जाने का गंभीर ख़तरा रहता है।",
      analogy: "दीवारों की दरारों में उगने वाली कमज़ोर जंगली झाड़ियों की तरह, जो अचानक टूटकर गंभीर नुकसान कर सकती हैं।",
      nextSteps: [
        "बिना किसी देरी के तुरंत ऑप्थैल्मोलॉजिस्ट या रेटिना क्लिनिक से आपातकालीन परामर्श लें।",
        "लेज़र उपचार और आधुनिक इंजेक्शन (Anti-VEGF) दृष्टि की रक्षा करने में प्रभावी हैं।",
        "डॉक्टर की सलाह तक भारी वजन उठाने और आँखों पर दबाव डालने वाली गतिविधियों से बचें।",
      ],
      urgency: "तत्काल विशेषज्ञ मूल्यांकन आवश्यक",
    },
    te: {
      badge: "గ్రేడ్ 4 • ముదిరిన స్థాయి (ప్రొలిఫరేటివ్)",
      title: "ముదిరిన డయాబెటిక్ రెటినోపతి",
      whatModelPredicted: "కంటిలో అత్యంత బలహీనమైన కొత్త రక్తనాళాలు ఏర్పడిన సంకేతాలను కంప్యూటర్ మోడల్ గుర్తించింది.",
      everydayExplanation:
        "ఆక్సిజన్ అందకపోవడంతో కంటిలో బలహీనమైన కొత్త రక్తనాళాలు పెరుగుతున్నాయి. ఇవి తేలికగా పగిలి కంటి లోపల రక్తస్రావం కలిగించి చూపును కోల్పోయే తీవ్ర ప్రమాదం కలిగిస్తాయి.",
      analogy: "గోడ పగుళ్లలో పెరిగే బలహీనమైన పిచ్చి మొక్కల వంటివి; ఇవి తెగి తీవ్రమైన నష్టాన్ని కలిగించవచ్చు.",
      nextSteps: [
        "వెంటనే రెటీనా నిపుణుడిని సంప్రదించి అత్యవసర చికిత్స పొందండి.",
        "లేజర్ చికిత్స మరియు ఇంజెక్షన్ల (Anti-VEGF) ద్వారా చూపును కాపాడుకోవచ్చు.",
        "వైద్యుడు అనుమతించే వరకు బరువైన వస్తువులు ఎత్తడం లాంటివి చేయవద్దు.",
      ],
      urgency: "అత్యవసర నిపుణుల సంప్రదింపు అవసరం",
    },
  },
};

export const HEATMAP_EXPLANATIONS = {
  en: {
    title: "Understanding the Glowing Heatmap",
    whatItRepresentsTitle: "What the Heatmap Shows",
    whatItRepresentsText:
      "The colorful glowing overlay is a computer attention map (Grad-CAM). It highlights the exact spots in the photograph where the artificial intelligence focused its attention when calculating the prediction score.",
    colorGuideTitle: "Color Guide",
    colorRed: "Red & Orange: Areas of high computer focus (features that influenced the score the most).",
    colorYellowGreen: "Yellow & Green: Moderate focus areas.",
    colorBlue: "Blue & Dark: Background areas that had little influence on the score.",
    whatItCannotProveTitle: "What the Heatmap CANNOT Prove",
    limits: [
      "It does NOT prove that disease is definitely present.",
      "It does NOT outline real biological disease borders, actual bleeding edges, or lesions.",
      "It is NOT a medical scan, X-ray, or biopsy — it only shows computer mathematical focus.",
    ],
    doctorRoleTitle: "Why a Doctor Must Examine Your Eye",
    doctorRoleText:
      "A photograph only captures the surface of your retina at one moment. A licensed eye doctor uses high-magnification slit lamps, 3D ophthalmoscopes, and dilated lenses to inspect depth, peripheral retina, and eye pressure that no 2D photo or AI model can evaluate.",
  },
  ta: {
    title: "வண்ண வெப்ப வரைபடத்தை (Heatmap) புரிந்து கொள்ளுதல்",
    whatItRepresentsTitle: "இந்த வரைபடம் எதைக் காட்டுகிறது?",
    whatItRepresentsText:
      "இந்த வண்ணமயமான படம் என்பது கணினியின் கவன வரைபடம் (Grad-CAM). கணினி மாதிரி இந்த புகைப்படத்தை ஆய்வு செய்து முடிவை கணிக்கும் போது, கண்ணின் எந்தெந்த பகுதிகளை அதிகமாக கவனித்தது என்பதையே இது காட்டுகிறது.",
    colorGuideTitle: "வண்ணங்களின் வழிகாட்டி",
    colorRed: "சிவப்பு & ஆரஞ்சு: கணினியின் அதிக கவனத்தைப் பெற்ற பகுதிகள் (முடிவை அதிகம் தீர்மானித்தவை).",
    colorYellowGreen: "மஞ்சள் & பச்சை: நடுத்தர கவனத்தைப் பெற்ற பகுதிகள்.",
    colorBlue: "நீலம் & கருமை: கணினி பெரிதாக கவனிக்காத பின்னணிப் பகுதிகள்.",
    whatItCannotProveTitle: "இந்த வரைபடம் எதை நிரூபிக்காது?",
    limits: [
      "இது உங்களுக்கு உறுதியாக நோய் இருப்பதையோ அல்லது இல்லையென்பதையோ உறுதிப்படுத்தாது (நிரூபிக்காது).",
      "இது உண்மையான இரத்தக் கசிவு அல்லது காயங்களின் துல்லியமான எல்லைகளைக் குறிக்காது.",
      "இது ஒரு எக்ஸ்-ரே அல்லது பயாப்ஸி போன்ற உண்மையான பரிசோதனை அல்ல; கணினியின் கணித கவனம் மட்டுமே.",
    ],
    doctorRoleTitle: "மருத்துவர் பரிசோதனை ஏன் கட்டாயம்?",
    doctorRoleText:
      "ஒரு புகைப்படம் கண்ணின் ஒரு பகுதியை மட்டுமே காட்டுகிறது. உரிமம் பெற்ற கண் மருத்துவர் மட்டுமே சிறப்பு லென்ஸ்கள் மற்றும் கருவிகள் மூலம் விழித்திரையின் ஆழம், விளிம்புகள் மற்றும் கண் அழுத்தத்தை முழுமையாக பரிசோதிக்க முடியும்.",
  },
  hi: {
    title: "रंगीन हीटमैप (Heatmap) को समझना",
    whatItRepresentsTitle: "हीटमैप क्या दर्शाता है?",
    whatItRepresentsText:
      "यह रंगीन आवरण कंप्यूटर का ध्यान नक्शा (Grad-CAM) है। यह तस्वीर के उन सटीक हिस्सों को उजागर करता है जहाँ कृत्रिम बुद्धिमत्ता (AI) ने स्कोर की गणना करते समय सबसे अधिक ध्यान केंद्रित किया।",
    colorGuideTitle: "रंगों की निर्देशिका",
    colorRed: "लाल और नारंगी: कंप्यूटर के उच्च ध्यान वाले क्षेत्र (जिन्होंने परिणाम को सबसे अधिक प्रभावित किया)।",
    colorYellowGreen: "पीला और हरा: मध्यम ध्यान वाले क्षेत्र।",
    colorBlue: "नीला और गहरा: पृष्ठभूमि क्षेत्र जिनका परिणाम पर बहुत कम प्रभाव पड़ा।",
    whatItCannotProveTitle: "हीटमैप क्या सिद्ध नहीं कर सकता?",
    limits: [
      "यह निश्चित रूप से सिद्ध नहीं करता कि बीमारी मौजूद है।",
      "यह वास्तविक जैविक बीमारी की सीमाओं या घाव के किनारों को रेखांकित नहीं करता है।",
      "यह कोई मेडिकल स्कैन, एक्स-रे या बायोप्सी नहीं है — यह केवल कंप्यूटर का गणितीय ध्यान है।",
    ],
    doctorRoleTitle: "डॉक्टर द्वारा परीक्षण क्यों आवश्यक है?",
    doctorRoleText:
      "एक तस्वीर केवल एक पल में रेटिना की सतह को कैद करती है। एक योग्य नेत्र रोग विशेषज्ञ पुतली फैलाकर सूक्ष्मदर्शी और विशेष लेंसों से गहराई, किनारों और आँखों के दबाव की व्यापक जाँच करता है।",
  },
  te: {
    title: "రంగుల హీట్‌మ్యాప్ (Heatmap) గురించి అవగాహన",
    whatItRepresentsTitle: "ఈ మ్యాప్ ఏమి చూపుతుంది?",
    whatItRepresentsText:
      "ఈ రంగుల చిత్రం కంప్యూటర్ శ్రద్ధ మ్యాప్ (Grad-CAM). ఫలితాన్ని నిర్ణయించేటప్పుడు ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ ఫోటోలోని ఏయే భాగాలపై ఎక్కువ దృష్టి పెట్టిందో ఇది చూపుతుంది.",
    colorGuideTitle: "రంగుల మార్గదర్శి",
    colorRed: "ఎరుపు & నారింజ: కంప్యూటర్ అత్యధిక దృష్టి పెట్టిన భాగాలు (ఫలితాన్ని ఎక్కువగా ప్రభావితం చేసినవి).",
    colorYellowGreen: "పసుపు & ఆకుపచ్చ: మధ్యస్థ శ్రద్ధ గల భాగాలు.",
    colorBlue: "నీలం & చీకటి: ఫలితంపై తక్కువ ప్రభావం చూపిన నేపథ్య భాగాలు.",
    whatItCannotProveTitle: "ఈ మ్యాప్ ఏమి నిరూపించదు?",
    limits: [
      "ఇది వ్యాధి ఖచ్చితంగా ఉందని లేదా లేదని నిరూపించదు.",
      "ఇది అసలైన వ్యాధి సరిహద్దులను లేదా గాయాలను గీసి చూపదు.",
      "ఇది ఎక్స్-రే లేదా బయాప్సీ వంటి వైద్య పరీక్ష కాదు; కంప్యూటర్ గణిత శ్రద్ధ మాత్రమే.",
    ],
    doctorRoleTitle: "వైద్యుని పరీక్ష ఎందుకు తప్పనిసరి?",
    doctorRoleText:
      "ఫోటో కంటి ఉపరితలాన్ని మాత్రమే చూపుతుంది. అర్హత కలిగిన కంటి వైద్యుడు మాత్రమే ప్రత్యేక కటకాల ద్వారా కంటి లోతు, అంచులు మరియు కంటి ఒత్తిడిని సమగ్రంగా పరిశీలించగలరు.",
  },
};

export const EMERGENCY_WARNINGS = {
  en: {
    title: "Urgent Warning Signs — When to Seek Immediate Emergency Care",
    intro:
      "Regardless of what any computer model predicts, seek immediate emergency eye care if you experience any of the following symptoms:",
    symptoms: [
      "Sudden loss of vision or sudden blurring in one or both eyes.",
      "A dark curtain, veil, or shadow spreading across your field of vision.",
      "A sudden shower of dark floating spots, webs, or flashes of light.",
      "Severe eye pain, redness, nausea, or seeing rainbow halos around lights.",
    ],
    instruction:
      "Do not wait for a routine appointment. Go to an emergency room or emergency eye clinic immediately.",
  },
  ta: {
    title: "அவசர எச்சரிக்கை அறிகுறிகள் — உடனடியாக மருத்துவமனை செல்ல வேண்டிய சூழல்",
    intro:
      "கணினி மாதிரி என்ன முடிவு காட்டினாலும், கீழ்க்கண்ட அறிகுறிகள் உங்களுக்கு தோன்றினால் உடனடியாக அவசர கண் மருத்துவ சிகிச்சை பெறவும்:",
    symptoms: [
      "ஒன்று அல்லது இரண்டு கண்களிலும் திடீரென பார்வை மங்குதல் அல்லது பார்வை பறிபோதல்.",
      "பார்வைக்கு குறுக்கே திடீரென ஒரு கரும் திரை அல்லது நிழல் விழுவது போன்ற உணர்வு.",
      "கண்ணில் திடீரென மின்னல் போன்ற ஒளிக்கீற்று அல்லது அதிகப்படியான கருப்பு புள்ளிகள் தோன்றுதல்.",
      "கடுமையான கண் வலி, சிவந்து போதல், அல்லது விளக்குகளைச் சுற்றி வானவில் வளையங்கள் தெரிதல்.",
    ],
    instruction:
      "வழக்கமான பரிசோதனைக்காக காத்திருக்க வேண்டாம்; உடனடியாக அவசர கண் மருத்துவ சிகிச்சைப் பிரிவை அணுகவும்.",
  },
  hi: {
    title: "आपातकालीन चेतावनी संकेत — तुरंत आपातकालीन चिकित्सा सहायता कब लें",
    intro:
      "कंप्यूटर मॉडल कोई भी परिणाम दिखाए, यदि आपको निम्नलिखित में से कोई भी लक्षण महसूस हो तो तुरंत आपातकालीन नेत्र चिकित्सा लें:",
    symptoms: [
      "एक या दोनों आँखों की दृष्टि अचानक चली जाना या गंभीर रूप से धुंधली होना।",
      "दृष्टि के सामने अचानक कोई काला पर्दा, छाया या धब्बा फैलना।",
      "आँखों के सामने अचानक चमकती रोशनी (फ़्लैश) या तैरते हुए काले धब्बे (फ्लोटर्स) दिखना।",
      "आँख में अत्यधिक दर्द, लालिमा, मतली, या रोशनी के चारों ओर इंद्रधनुषी घेरे दिखना।",
    ],
    instruction:
      "नियमित अपॉइंटमेंट का इंतज़ार न करें। तुरंत नजदीकी आपातकालीन नेत्र चिकित्सालय जाएं।",
  },
  te: {
    title: "అత్యవసర హెచ్చరిక సంకేతాలు — తక్షణ అత్యవసర వైద్య సంరక్షణ ఎప్పుడు పొందాలి",
    intro:
      "కంప్యూటర్ మోడల్ ఎలాంటి ఫలితాన్ని చూపించినప్పటికీ, కింది లక్షణాలు కనిపిస్తే వెంటనే అత్యవసర కంటి చికిత్స పొందండి:",
    symptoms: [
      "ఒకటి లేదా రెండు కళ్ళలో అకస్మాత్తుగా చూపు కోల్పోవడం లేదా మసకబారడం.",
      "చూపుకు అడ్డంగా చీకటి తెర లేదా నీడ పడుతున్నట్లు అనిపించడం.",
      "కంటి ముందు అకస్మాత్తుగా మెరుపులు లేదా నల్లటి మచ్చలు కనిపించడం.",
      "తీవ్రమైన కంటి నొప్పి, ఎరుపుదనం లేదా కాంతి చుట్టూ ఇంద్రధనస్సు వలయాలు కనిపించడం.",
    ],
    instruction:
      "సాధారణ అపాయింట్‌మెంట్ కోసం వేచి ఉండకండి. వెంటనే అత్యవసర కంటి ఆసుపత్రికి వెళ్ళండి.",
  },
};

export const UI_STRINGS = {
  en: {
    sectionHeading: "Understand Your Result",
    sectionSubheading:
      "Plain-language explanation of this retinal scan, visual attention, and evidence-based guidance.",
    languageToggleLabel: "Select Language",
    readAloud: "Listen (Read Aloud)",
    pauseAudio: "Pause Audio",
    resumeAudio: "Resume Audio",
    stopAudio: "Stop Audio",
    audioPlaying: "Reading aloud...",
    audioPaused: "Audio paused.",
    audioFinished: "Audio finished.",
    audioUnavailable:
      "Read-aloud text-to-speech is not supported or enabled in this browser. Please review the text above.",
    voiceUnavailable:
      "Voice synthesizer is not installed for this language on your device. Please read the text above.",
    tamilVoiceUnavailable:
      "Tamil voice synthesizer is not installed on this device. Playing in default voice or please read the text.",
    confidenceTitle: "Model Score & Certainty",
    lowConfidenceWarning:
      "Low Confidence Notice: The model's calculated score for this image is modest (< 60%). The photograph may be slightly dark, off-center, or out of focus. Never rely on an uncertain score for reassurance.",
    disclaimerBannerTitle: "Educational & Research Notice",
    disclaimerBannerText:
      "This explanation is strictly for educational understanding and is NOT personal medical advice. It cannot substitute for a clinical evaluation by a licensed ophthalmologist or optometrist.",
    noPrediction: "No prediction data is available to explain.",
  },
  ta: {
    sectionHeading: "உங்கள் முடிவை புரிந்து கொள்ளுங்கள்",
    sectionSubheading:
      "விழித்திரை ஆய்வு முடிவு, கவன வரைபடம் மற்றும் அடுத்த கட்ட நடவடிக்கைகள் பற்றிய எளிய விளக்கம்.",
    languageToggleLabel: "மொழியைத் தேர்ந்தெடுக்கவும்",
    readAloud: "கேளுங்கள் (ஒலி வடிவம்)",
    pauseAudio: "நிறுத்துக",
    resumeAudio: "தொடர்க",
    stopAudio: "முடிக்க",
    audioPlaying: "ஒலி வாசிக்கப்படுகிறது...",
    audioPaused: "ஒலி தற்காலிகமாக நிறுத்தப்பட்டது.",
    audioFinished: "ஒலி வாசிப்பு முடிந்தது.",
    audioUnavailable:
      "இந்த உலாவியில் ஒலி வாசிப்பு (Text-to-Speech) வசதி இல்லை. மேற்கண்ட உரையை நேரடியாக வாசிக்கவும்.",
    voiceUnavailable:
      "இந்த மொழிக்கான குரல் வசதி இந்த சாதனத்தில் இல்லை. மேற்கண்ட உரையை நேரடியாக வாசிக்கவும்.",
    tamilVoiceUnavailable:
      "இந்த சாதனத்தில் தமிழ் குரல் வசதி கிடைக்கவில்லை. மேற்கண்ட தமிழ் உரையை நேரடியாக வாசிக்கவும்.",
    confidenceTitle: "மாதிரி மதிப்பெண் மற்றும் உறுதிப்பாடு",
    lowConfidenceWarning:
      "குறைந்த உறுதிப்பாடு அறிவிப்பு: இந்த புகைப்படத்திற்கான கணினி கணிப்பு உறுதிப்பாடு குறைவாக உள்ளது (< 60%). புகைப்படம் மங்கலாக அல்லது வெளிச்சம் குறைவாக இருக்கலாம். இதை வைத்து எந்த முடிவும் எடுக்க வேண்டாம்.",
    disclaimerBannerTitle: "கல்வி மற்றும் ஆராய்ச்சி அறிவிப்பு",
    disclaimerBannerText:
      "இந்த விளக்கம் கல்வி புரிதலுக்காக மட்டுமே; இது தனிப்பட்ட மருத்துவ ஆலோசனை அல்ல. உரிமம் பெற்ற கண் மருத்துவ நிபுணரின் நேரடி பரிசோதனைக்கு இது ஈடாகாது.",
    noPrediction: "விளக்குவதற்கு எந்த கணிப்பு தகவலும் கிடைக்கவில்லை.",
  },
  hi: {
    sectionHeading: "अपने परिणाम को समझें",
    sectionSubheading:
      "इस रेटिनल स्कैन, कंप्यूटर के ध्यान और साक्ष्य-आधारित मार्गदर्शन की सरल भाषा में व्याख्या।",
    languageToggleLabel: "भाषा चुनें",
    readAloud: "सुनें (बोलकर पढ़ें)",
    pauseAudio: "रोकें",
    resumeAudio: "जारी रखें",
    stopAudio: "समाप्त करें",
    audioPlaying: "प्रतिक्रिया सुनाई जा रही है...",
    audioPaused: "ऑडियो रुका हुआ है।",
    audioFinished: "ऑडियो पूरा हुआ।",
    audioUnavailable:
      "इस ब्राउज़र में टेक्स्ट-टू-स्पीच समर्थित नहीं है। कृपया ऊपर दिया गया पाठ पढ़ें।",
    voiceUnavailable:
      "आपके उपकरण पर इस भाषा के लिए आवाज़ स्थापित नहीं है। कृपया ऊपर दिया गया पाठ पढ़ें।",
    tamilVoiceUnavailable:
      "आपके उपकरण पर इस भाषा की आवाज़ नहीं मिली। कृपया ऊपर दिया गया पाठ पढ़ें।",
    confidenceTitle: "मॉडल स्कोर और निश्चितता",
    lowConfidenceWarning:
      "कम निश्चितता सूचना: इस छवि के लिए मॉडल का अनुमानित स्कोर सामान्य (< 60%) है। तस्वीर धुंधली या कम रोशनी वाली हो सकती है। किसी अनिश्चित स्कोर पर भरोसा न करें।",
    disclaimerBannerTitle: "शैक्षिक एवं अनुसंधान सूचना",
    disclaimerBannerText:
      "यह व्याख्या केवल शैक्षिक समझ के लिए है और व्यक्तिगत चिकित्सा सलाह नहीं है। यह किसी योग्य नेत्र विशेषज्ञ द्वारा नैदानिक परीक्षण का विकल्प नहीं हो सकती।",
    noPrediction: "समझाने के लिए कोई परिणाम उपलब्ध नहीं है।",
  },
  te: {
    sectionHeading: "మీ ఫలితాన్ని అర్థం చేసుకోండి",
    sectionSubheading:
      "ఈ రెటీనా స్కాన్, కంప్యూటర్ శ్రద్ధ మరియు మార్గదర్శకాల గురించి సరళమైన వివరణ.",
    languageToggleLabel: "భాషను ఎంచుకోండి",
    readAloud: "వినండి (వాయిస్ ద్వారా)",
    pauseAudio: "ఆపు",
    resumeAudio: "కొనసాగించు",
    stopAudio: "ముగించు",
    audioPlaying: "సమాధానం చదవబడుతోంది...",
    audioPaused: "ఆడియో పాజ్ చేయబడింది.",
    audioFinished: "ఆడియో పూర్తయింది.",
    audioUnavailable:
      "ఈ బ్రౌజర్‌లో టెక్స్ట్-టు-స్పీచ్ సదుపాయం లేదు. దయచేసి పై వచనాన్ని చదవండి.",
    voiceUnavailable:
      "ఈ పరికరంలో ఈ భాష కోసం వాయిస్ ఇన్‌స్టాల్ చేయబడలేదు. దయచేసి పై వచనాన్ని చదవండి.",
    tamilVoiceUnavailable:
      "ఈ పరికరంలో ఈ భాష వాయిస్ అందుబాటులో లేదు. దయచేసి పై వచనాన్ని చదవండి.",
    confidenceTitle: "మోడల్ స్కోరు & ఖచ్చితత్వం",
    lowConfidenceWarning:
      "తక్కువ ఖచ్చితత్వ నోటీసు: ఈ చిత్రానికి మోడల్ లెక్కించిన స్కోరు తక్కువగా ఉంది (< 60%). ఫోటో మసకగా లేదా వెలుతురు తక్కువగా ఉండవచ్చు. అనిశ్చిత స్కోర్‌పై ఆధారపడవద్దు.",
    disclaimerBannerTitle: "విద్యా & పరిశోధన నోటీసు",
    disclaimerBannerText:
      "ఈ వివరణ కేవలం అవగాహన కోసం మాత్రమే మరియు ఇది వైద్య సలహా కాదు. ఇది కంటి నిపుణుడి ప్రత్యక్ష పరీక్షకు ప్రత్యామ్నాయం కాదు.",
    noPrediction: "వివరించడానికి ఎలాంటి ఫలితం అందుబాటులో లేదు.",
  },
};
