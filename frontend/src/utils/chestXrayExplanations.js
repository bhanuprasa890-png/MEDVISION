/**
 * Patient-Friendly Educational Explanations and Clinical Definitions
 * for Chest X-Ray (CXR) Thoracic Analysis in MEDVISION.
 *
 * Covers all 18 thoracic pathologies supported by the TorchXRayVision DenseNet-121 model:
 * 1. Atelectasis
 * 2. Consolidation
 * 3. Infiltration
 * 4. Pneumothorax
 * 5. Edema
 * 6. Emphysema
 * 7. Fibrosis
 * 8. Effusion
 * 9. Pneumonia
 * 10. Pleural_Thickening (Pleural Thickening)
 * 11. Cardiomegaly
 * 12. Nodule
 * 13. Mass
 * 14. Hernia
 * 15. Lung Lesion (Lung_Lesion)
 * 16. Fracture
 * 17. Lung Opacity (Lung_Opacity)
 * 18. Enlarged Cardiomediastinum (Enlarged_Cardiomediastinum)
 *
 * Provides authentic multilingual guidance in English (en), Tamil (ta), Hindi (hi), and Telugu (te).
 * Strictly preserves non-diagnostic safety boundaries, lay analogies, Grad-CAM limitations,
 * uncalibrated score interpretations, and emergency red-flag warnings.
 */

export const CXR_PATHOLOGY_EXPLANATIONS = {
  Atelectasis: {
    clinicalLabel: "Atelectasis",
    en: {
      title: "Atelectasis (Partial Lung Air Sac Deflation)",
      badge: "Thoracic Finding • Air Sac Collapse",
      whatItMeans:
        "Tiny air sacs (alveoli) inside part of your lung have deflated or flattened instead of staying open and filled with air. This often happens after shallow breathing, bed rest, or a temporary mucus plug.",
      whatModelSaw:
        "The computer model noticed a localized area where lung tissue appears denser and less filled with air than surrounding regions. This is a pattern observation, not a confirmed disease diagnosis.",
      analogy: "Like a party balloon that has partially lost its air, making that small section compact rather than buoyant.",
      nextSteps: [
        "Discuss this finding with your doctor at your next scheduled visit.",
        "Deep breathing exercises and gentle walking often help re-inflate deflated air sacs.",
        "A doctor will listen to your chest with a stethoscope to evaluate how air is moving.",
      ],
      careCategory: "Routine Physician Review",
    },
    ta: {
      title: "அடெலெக்டாசிஸ் (நுரையீரல் காற்றுப் பைகள் சுருங்குதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • காற்றுப் பை சுருக்கம்",
      whatItMeans:
        "நுரையீரலில் உள்ள சிறிய காற்றுப் பைகள் (அல்வியோலை) காற்றில்லாமல் சுருங்கிவிட்டன அல்லது மூடிக்கொண்டன. ஆழமற்ற சுவாசம், படுக்கையில் ஓய்வெடுத்தல் அல்லது சளி அடைப்பால் இது பொதுவாக ஏற்படுகிறது.",
      whatModelSaw:
        "கணினி மாதிரி நுரையீரலின் ஒரு பகுதியில் காற்று குறைவாகவும் திசுக்கள் சுருங்கியும் இருப்பதைக் குறிக்கும் அடர்த்தி அமைப்பைக் கண்டறிந்துள்ளது. இது நேரடி நோய் உறுதிப்படுத்தல் அல்ல.",
      analogy: "காற்று வெளியேறி லேசாக சுருங்கிய சிறிய பலூன் போன்ற நிலை இது.",
      nextSteps: [
        "உங்கள் மருத்துவரை அணுகி இந்த எக்ஸ்-ரே முடிவை காண்பியுங்கள்.",
        "ஆழமாக மூச்சை உள்ளிழுத்து வெளிவிடும் மூச்சுப் பயிற்சிகள் காற்றுப் பைகளை மீண்டும் விரியச் செய்ய உதவும்.",
        "மருத்துவர் ஸ்டெதாஸ்கோப் மூலம் உங்கள் நுரையீரல் சுவாச ஒலிகளை பரிசோதிப்பார்.",
      ],
      careCategory: "மருத்துவ ஆலோசனை பரிந்துரைக்கப்படுகிறது",
    },
    hi: {
      title: "एटिलेक्टेसिस (फेफड़ों की वायु-थैलियों का सिकुड़ना)",
      badge: "वक्षीय निष्कर्ष • वायु-कोशिका संकुचन",
      whatItMeans:
        "फेफड़ों के भीतर मौजूद छोटी वायु-थैलियां (एल्वियोली) सामान्य रूप से फूलने के बजाय आंशिक रूप से सिकुड़ या पिचक गई हैं। उथली सांस लेने, लंबे समय तक लेटे रहने या बलगम की रुकावट से ऐसा हो सकता है।",
      whatModelSaw:
        "कंप्यूटर मॉडल ने फेफड़े के एक हिस्से में हवा की कमी और ऊतक के घनत्व का पैटर्न देखा है। यह केवल एक गणितीय पहचान है, अंतिम नैदानिक पुष्टि नहीं।",
      analogy: "एक गुब्बारे की तरह जिसकी हवा थोड़ी निकल जाने से वह पिचक जाता है।",
      nextSteps: [
        "अपने चिकित्सक से मिलकर इस एक्स-रे परिणाम पर चर्चा करें।",
        "गहरी सांस लेने के व्यायाम और हल्का चलना वायु-थैलियों को दोबारा खोलने में मदद कर सकते हैं।",
        "डॉक्टर स्टेथोस्कोप से फेफड़ों की सांस की आवाज़ सुनकर स्थिति की जाँच करेंगे।",
      ],
      careCategory: "चिकित्सक से परामर्श अनुशंसित",
    },
    te: {
      title: "అటెలెక్టాసిస్ (ఊపిరితిత్తుల వాయుకోశాల సంకోచం)",
      badge: "ఛాతీ పరిశీలన • వాయుకోశాల కుదింపు",
      whatItMeans:
        "ఊపిరితిత్తులలోని చిన్న గాలి గదులు (అల్వియోలీ) గాలితో నిండకుండా కొంత భాగం ముడుచుకుపోయాయి. తక్కువగా శ్వాస తీసుకోవడం, పడకపై ఎక్కువసేపు విశ్రాంతి తీసుకోవడం వల్ల ఇది జరగవచ్చు.",
      whatModelSaw:
        "కంప్యూటర్ మోడల్ ఊపిరితిత్తులలో గాలి తక్కువగా ఉన్న భాగాన్ని గుర్తించింది. ఇది రోగ నిర్ధారణ కాదు, కేవలం నమూనా గుర్తింపు మాత్రమే.",
      analogy: "గాలి తగ్గి పాక్షికంగా ముడుచుకుపోయిన బెలూన్ లాంటి స్థితి ఇది.",
      nextSteps: [
        "మీ వైద్యుడిని సంప్రదించి ఈ ఎక్స్-రే ఫలితాన్ని చూపించండి.",
        "లోతైన శ్వాస వ్యాయామాలు ఊపిరితిత్తుల గదులను మళ్లీ తెరవడానికి సహాయపడతాయి.",
        "వైద్యుడు స్టెతస్కోప్ ద్వారా శ్వాస శబ్దాలను ప్రత్యక్షంగా పరీక్షిస్తారు.",
      ],
      careCategory: "వైద్యుని సంప్రదింపు సిఫార్సు చేయబడింది",
    },
  },

  Consolidation: {
    clinicalLabel: "Consolidation",
    en: {
      title: "Consolidation (Solidified / Fluid-Filled Air Spaces)",
      badge: "Thoracic Finding • Alveolar Filling",
      whatItMeans:
        "Normally sponge-like lung air sacs have filled with fluid, pus, or inflammatory cellular debris, making that section of lung appear solid and opaque on X-rays rather than dark and airy.",
      whatModelSaw:
        "The model identified a dense, non-transparent patch in the lung field where air would normally appear dark. Consolidation commonly occurs with pneumonia, infections, or inflammation.",
      analogy: "Like a dry, airy sponge that has soaked up water, becoming heavy and solid.",
      nextSteps: [
        "Seek a clinical consultation promptly to check for signs of respiratory infection.",
        "Inform your doctor if you have had a fever, productive cough, or chills.",
        "Do not start antibiotics without an authorized medical prescription.",
      ],
      careCategory: "Prompt Medical Evaluation",
    },
    ta: {
      title: "கன்சாலிடேஷன் (நுரையீரல் காற்றுப் பைகளில் திரவம் நிறைதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • திரவ தேக்கம்",
      whatItMeans:
        "காற்றினால் நிறைந்திருக்க வேண்டிய பஞ்சு போன்ற நுரையீரல் பகுதிகள் சளி, சீழ் அல்லது அழற்சி திரவத்தால் நிரம்பி கடினமாகியுள்ளன.",
      whatModelSaw:
        "கணினி மாதிரி எக்ஸ்-ரே படத்தில் வழக்கமாக இருட்டாகத் தெரிய வேண்டிய காற்றிடத்தில் அடர்த்தியான வெள்ளை நிற திரவ நிழலைக் கண்டறிந்துள்ளது. இது நிமோனியா அல்லது தொற்றுகளில் பொதுவாகக் காணப்படும்.",
      analogy: "தண்ணீரை உறிஞ்சி கனமாகிவிட்ட பஞ்சு போன்ற நிலை.",
      nextSteps: [
        "சுவாச தொற்று உள்ளதா என்பதை அறிய உடனடியாக மருத்துவரை அணுகவும்.",
        "காய்ச்சல், இருமல் அல்லது சளி உள்ளதா என்பதை மருத்துவரிடம் தெரிவிக்கவும்.",
        "மருத்துவரின் பரிந்துரை இல்லாமல் சுயமாக மாத்திரைகள் எடுக்க வேண்டாம்.",
      ],
      careCategory: "விரைவான மருத்துவ பரிசோதனை தேவை",
    },
    hi: {
      title: "कंसॉलिडेशन (फेफड़ों में तरल या बलगम का जमाव)",
      badge: "वक्षीय निष्कर्ष • तरल जमाव",
      whatItMeans:
        "फेफड़ों की स्पंज जैसी खाली वायु-थैलियां हवा के बजाय बलगम, मवाद या सूजन के तरल से भर गई हैं, जिससे वह हिस्सा एक्स-रे में ठोस और सफेद दिखाई देता है।",
      whatModelSaw:
        "मॉडल ने फेफड़े के क्षेत्र में एक घना, धुंधला धब्बा देखा है जहां सामान्यतः हवा होनी चाहिए। यह निमोनिया या संक्रमण का संकेत हो सकता है।",
      analogy: "पानी सोख चुके भारी और गीले स्पंज की तरह।",
      nextSteps: [
        "संक्रमण की जांच के लिए शीघ्र चिकित्सक से परामर्श लें।",
        "यदि आपको बुखार, खांसी या ठंड लग रही है तो डॉक्टर को बताएं।",
        "डॉक्टर की सलाह के बिना कोई एंटीबायोटिक न लें।",
      ],
      careCategory: "शीघ्र चिकित्सीय मूल्यांकन",
    },
    te: {
      title: "కన్సాలిడేషన్ (ఊపిరితిత్తులలో ద్రవం నిండటం)",
      badge: "ఛాతీ పరిశీలన • ద్రవ నిల్వ",
      whatItMeans:
        "గాలితో నిండి ఉండాల్సిన ఊపిరితిత్తుల భాగాలు ఇన్ఫెక్షన్ లేదా శ్లేష్మ ద్రవంతో నిండిపోయి గట్టిపడ్డాయి.",
      whatModelSaw:
        "ఎక్స్-రేలో సాధారణంగా నల్లగా కనిపించాల్సిన గాలి ప్రదేశంలో దట్టమైన తెల్లటి మచ్చను కంప్యూటర్ గుర్తించింది. ఇది న్యుమోనియా లేదా ఇతర ఇన్ఫెక్షన్లలో కనిపిస్తుంది.",
      analogy: "నీటిని పీల్చుకుని బరువెక్కిన స్పాంజ్ లాంటి పరిస్థితి.",
      nextSteps: [
        "శ్వాసకోశ ఇన్ఫెక్షన్ల కోసం వెంటనే వైద్యుడిని సంప్రదించండి.",
        "జ్వరం, దగ్గు లేదా కఫం వంటి లక్షణాలు ఉంటే తెలియజేయండి.",
        "వైద్యుల ప్రిస్క్రిప్షన్ లేకుండా మందులు వాడవద్దు.",
      ],
      careCategory: "సత్వర వైద్య పరిశీలన అవసరం",
    },
  },

  Infiltration: {
    clinicalLabel: "Infiltration",
    en: {
      title: "Infiltration (Substance Accumulation in Lung Tissue)",
      badge: "Thoracic Finding • Infiltrate Density",
      whatItMeans:
        "An abnormal substance (such as inflammatory fluid, protein, or immune cells) has accumulated within the lung tissue, creating a cloudy, hazy appearance on the radiograph.",
      whatModelSaw:
        "The neural network detected hazy patches of increased radiographic density. This pattern can accompany mild chest colds, bronchitis, allergies, or early infection.",
      analogy: "Like morning fog spreading across a clear landscape, making the background look diffuse.",
      nextSteps: [
        "Schedule a medical checkup to correlate this image with your symptoms.",
        "Stay well-hydrated and rest while awaiting your doctor's assessment.",
        "Report any persistent cough or chest discomfort to your healthcare team.",
      ],
      careCategory: "Medical Consultation Advised",
    },
    ta: {
      title: "இன்பில்ட்ரேஷன் (நுரையீரல் திசுக்களில் நீர்மம் சேருதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • திசு அழற்சி",
      whatItMeans:
        "நுரையீரல் திசுக்களுக்குள் அழற்சி திரவம் அல்லது நோய் எதிர்ப்பு செல்கள் சேர்ந்து எக்ஸ்-ரே படத்தில் பனிமூட்டம் போன்ற மங்கலான தோற்றத்தை ஏற்படுத்துகின்றன.",
      whatModelSaw:
        "நுரையீரலில் லேசான பனி போன்ற அடர்த்தி அதிகரிப்பை மாதிரி கண்டறிந்துள்ளது. இது சளி, மூச்சுக்குழாய் அழற்சி அல்லது லேசான தொற்றுகளில் ஏற்படலாம்.",
      analogy: "தெளிவான வானிலையில் லேசான காலை பனிமூட்டம் படர்வது போன்றது.",
      nextSteps: [
        "உங்கள் மருத்துவரை சந்தித்து பரிசோதித்துக் கொள்ளவும்.",
        "நிறைய தண்ணீர் குடித்து ஓய்வெடுக்கவும்.",
        "தொடர் இருமல் அல்லது மார்பு அசௌகரியம் இருந்தால் மருத்துவரிடம் தெரிவிக்கவும்.",
      ],
      careCategory: "மருத்துவர் ஆலோசனை பரிந்துரைக்கப்படுகிறது",
    },
    hi: {
      title: "इन्फिल्ट्रेशन (फेफड़ों के ऊतकों में सूजन या तरल)",
      badge: "वक्षीय निष्कर्ष • ऊतक घनत्व",
      whatItMeans:
        "फेफड़ों के ऊतकों में असामान्य तरल या सूजन की कोशिकाएं जमा हो गई हैं, जिससे एक्स-रे में हल्का धुंधलापन दिखाई दे रहा है।",
      whatModelSaw:
        "मॉडल ने फेफड़े के ऊतक में धुंधलेपन का पैटर्न पहचाना है, जो सामान्य सर्दी, ब्रोंकाइटिस या शुरुआती संक्रमण में देखा जा सकता है।",
      analogy: "साफ शीशे पर जमी हल्की धुंध की तरह।",
      nextSteps: [
        "अपने लक्षणों के साथ इस परिणाम का मिलान कराने के लिए डॉक्टर से मिलें।",
        "भरपूर पानी पिएं और पर्याप्त आराम करें।",
        "लगातार खांसी या बेचैनी होने पर डॉक्टर को सूचित करें।",
      ],
      careCategory: "चिकित्सकीय परामर्श अनुशंसित",
    },
    te: {
      title: "ఇన్‌ఫిల్ట్రేషన్ (ఊపిరితిత్తుల కణజాలంలో ద్రవ చేరిక)",
      badge: "ఛాతీ పరిశీలన • మసకబారిన కణజాలం",
      whatItMeans:
        "ఊపిరితిత్తుల కణజాలంలో వాపు ద్రవం చేరడం వల్ల ఎక్స్-రేలో మసకబారినట్లు కనిపిస్తుంది.",
      whatModelSaw:
        "కంప్యూటర్ మోడల్ ఊపిరితిత్తులలో మసకబారిన నమూనాను గుర్తించింది. ఇది బ్రోన్కైటిస్ లేదా ప్రారంభ ఇన్ఫెక్షన్లలో కనిపిస్తుంది.",
      analogy: "స్పష్టమైన అద్దంపై పొగమంచు పట్టినట్లు ఉండే స్థితి.",
      nextSteps: [
        "మీ లక్షణాల ఆధారంగా పూర్తి పరీక్ష కోసం వైద్యుడిని సంప్రదించండి.",
        "మంచి నీరు తాగుతూ తగినంత విశ్రాంతి తీసుకోండి.",
        "దగ్గు లేదా ఛాతీలో అసౌకర్యం ఉంటే వైద్యునికి తెలపండి.",
      ],
      careCategory: "వైద్య సంప్రదింపు సిఫార్సు చేయబడింది",
    },
  },

  Pneumothorax: {
    clinicalLabel: "Pneumothorax",
    en: {
      title: "Pneumothorax (Air Outside the Lung / Collapsed Lung)",
      badge: "Thoracic Finding • Pleural Air Space",
      whatItMeans:
        "Air has leaked into the space between your lung and the chest wall (the pleural space). This trapped air puts pressure on the lung, preventing it from expanding normally.",
      whatModelSaw:
        "The model flagged an area showing a thin pleural line with an absence of normal lung vascular markings beyond it. This pattern suggests air trapped outside the lung parenchyma.",
      analogy: "Like air leaking inside the lining of a double-layered jacket, squeezing the inner layer inward.",
      nextSteps: [
        "Prompt medical evaluation by a physician or emergency provider is critical.",
        "If you feel sudden sharp chest pain or shortness of breath, seek emergency care immediately.",
        "Avoid air travel or scuba diving until fully cleared by a doctor.",
      ],
      careCategory: "Immediate Clinical Attention",
    },
    ta: {
      title: "நியூமோதோராக்ஸ் (நுரையீரல் உறைக்குள் காற்று புகுதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • உறைக்குள் காற்று",
      whatItMeans:
        "நுரையீரலுக்கும் மார்பு கூட்டுக்கும் இடைப்பட்ட உறைக்குள் காற்று கசிந்து தங்கியுள்ளது. இந்த அழுத்தம் நுரையீரலை சுருங்கச் செய்யலாம்.",
      whatModelSaw:
        "நுரையீரல் உறைக்கு வெளியே காற்று தேங்கியிருப்பதற்கான மெல்லிய கோட்டு அடையாளத்தை மாதிரி கவனித்துள்ளது.",
      analogy: "இரட்டை அடுக்கு உடையின் அடுக்குகளுக்குள் காற்று புகுந்து உள்பகுதியை அழுத்துவது போன்ற நிலை.",
      nextSteps: [
        "உடனடியாக மருத்துவ நிபுணரை அணுகி மார்பு பரிசோதனை செய்யவும்.",
        "திடீர் கடுமையான மார்பு வலி அல்லது மூச்சுத்திணறல் ஏற்பட்டால் அவசர சிகிச்சை பிரிவுக்குச் செல்லவும்.",
        "மருத்துவரின் அனுமதியின்றி விமானப் பயணம் செய்ய வேண்டாம்.",
      ],
      careCategory: "உடனடி மருத்துவ கவனிப்பு தேவை",
    },
    hi: {
      title: "न्यूमोथोरैक्स (फेफड़े और छाती की दीवार के बीच हवा)",
      badge: "वक्षीय निष्कर्ष • प्लूरल हवा",
      whatItMeans:
        "फेफड़े और छाती की दीवार के बीच की जगह (प्लूरल कैविटी) में हवा रिस गई है, जिससे फेफड़े पर दबाव पड़ता है।",
      whatModelSaw:
        "मॉडल ने फेफड़े की बाहरी परत के पास हवा के जमाव का पैटर्न देखा है। यह स्थिति फेफड़े के सामान्य फैलाव को बाधित कर सकती है।",
      analogy: "डबल लेयर जैकेट के अंदर हवा भर जाने से अंदरूनी हिस्से पर दबाव पड़ने जैसा।",
      nextSteps: [
        "शीघ्र चिकित्सीय जाँच अत्यंत आवश्यक है।",
        "यदि अचानक सीने में तेज दर्द या सांस लेने में तकलीफ हो, तो तुरंत आपातकालीन सेवा लें।",
        "डॉक्टर की सलाह के बिना हवाई यात्रा न करें।",
      ],
      careCategory: "तत्काल चिकित्सीय ध्यान",
    },
    te: {
      title: "న్యూమోథొరాక్స్ (ఛాతీ గోడ మధ్య గాలి చేరడం)",
      badge: "ఛాతీ పరిశీలన • ఊపిరితిత్తుల వెలుపల గాలి",
      whatItMeans:
        "ఊపిరితిత్తులకు మరియు ఛాతీ గోడకు మధ్య ఉండే ఖాళీలో గాలి లీక్ అయి చేరింది. ఇది ఊపిరితిత్తులపై ఒత్తిడిని కలిగిస్తుంది.",
      whatModelSaw:
        "ఊపిరితిత్తుల వెలుపల గాలి చేరిన నమూనాను కంప్యూటర్ మోడల్ గుర్తించింది.",
      analogy: "జాకెట్ పొరల మధ్య గాలి చేరి లోపలి భాగాన్ని నొక్కినట్లు ఉండే స్థితి.",
      nextSteps: [
        "వెంటనే వైద్యుడిని కలిసి పూర్తి పరీక్ష చేయించుకోండి.",
        "తీవ్రమైన ఛాతీ నొప్పి లేదా ఆయాసం వస్తే అత్యవసర విభాగాన్ని ఆశ్రయించండి.",
        "వైద్యుని అనుమతి లేకుండా విమాన ప్రయాణాలు చేయవద్దు.",
      ],
      careCategory: "తక్షణ వైద్య శ్రద్ధ అవసరం",
    },
  },

  Edema: {
    clinicalLabel: "Edema",
    en: {
      title: "Pulmonary Edema (Fluid in Lung Tissues)",
      badge: "Thoracic Finding • Fluid Congestion",
      whatItMeans:
        "Excess fluid has collected inside the tissues and air spaces of the lungs, commonly related to heart function, kidney conditions, or fluid overload.",
      whatModelSaw:
        "The AI recognized diffuse bat-wing or perihilar haziness indicative of fluid congestion around the central pulmonary vessels.",
      analogy: "Like soil in a garden that has become waterlogged after heavy rain.",
      nextSteps: [
        "Consult your cardiologist or primary care doctor promptly.",
        "Track whether your ankles are swollen or if breathing becomes harder when lying flat.",
        "Do not alter your fluid intake or heart medications without medical advice.",
      ],
      careCategory: "Prompt Clinical Review",
    },
    ta: {
      title: "பல்மோனரி எடிமா (நுரையீரல் நீர் வீக்கம்)",
      badge: "மார்பு கண்டுபிடிப்பு • நீர் தேக்கம்",
      whatItMeans:
        "நுரையீரலில் அதிகப்படியான நீர் சேர்ந்துள்ளது. இது பெரும்பாலும் இதய செயல்பாடு அல்லது சிறுநீரக காரணங்களால் ஏற்படுகிறது.",
      whatModelSaw:
        "நுரையீரலின் மைய இரத்தக் குழாய்களைச் சுற்றி நீர் தேங்கியிருப்பதற்கான பனி போன்ற நிழல் அமைப்பை மாதிரி கண்டறிந்துள்ளது.",
      analogy: "அதிக மழையால் நனைந்து நீர் தேங்கி நிற்கும் நிலம் போன்றது.",
      nextSteps: [
        "உடனடியாக உங்கள் இதய அல்லது பொது மருத்துவரை அணுகவும்.",
        "கால்களில் வீக்கம் உள்ளதா அல்லது படுக்கும் போது மூச்சு வாங்குகிறதா என்பதைக் கவனியுங்கள்.",
        "மருத்துவரின் ஆலோசனையின்றி மருந்துகளின் அளவை மாற்ற வேண்டாம்.",
      ],
      careCategory: "விரைவான மருத்துவ ஆய்வு தேவை",
    },
    hi: {
      title: "पल्मोनरी एडिमा (फेफड़ों में पानी का जमाव)",
      badge: "वक्षीय निष्कर्ष • द्रव संचय",
      whatItMeans:
        "फेफड़ों के ऊतकों और वायु-स्थानों में अतिरिक्त पानी/तरल जमा हो गया है, जो हृदय या गुर्दे की कार्यप्रणाली से संबंधित हो सकता है।",
      whatModelSaw:
        "मॉडल ने फेफड़ों के मध्य भाग में द्रव संचय (कंजेस्शन) का पैटर्न देखा है।",
      analogy: "अत्यधिक बारिश के बाद पानी से भरे हुए खेत की तरह।",
      nextSteps: [
        "शीघ्र अपने चिकित्सक या हृदय रोग विशेषज्ञ से परामर्श लें।",
        "पैरों में सूजन या लेटने पर सांस फूलने के लक्षणों पर ध्यान दें।",
        "डॉक्टर की सलाह के बिना पानी या दवाओं की खुराक में बदलाव न करें।",
      ],
      careCategory: "शीघ्र चिकित्सीय समीक्षा",
    },
    te: {
      title: "పల్మోనరీ ఎడెమా (ఊపిరితిత్తులలో నీరు చేరడం)",
      badge: "ఛాతీ పరిశీలన • ద్రవ రద్దీ",
      whatItMeans:
        "ఊపిరితిత్తుల కణజాలాలలో అధికంగా నీరు చేరింది. ఇది సాధారణంగా గుండె లేదా మూత్రపిండాల పనితీరుతో సంబంధం కలిగి ఉంటుంది.",
      whatModelSaw:
        "ఊపిరితిత్తులలో రక్తనాళాల చుట్టూ నీరు నిలిచిపోయిన మసక నమూనాను AI గుర్తించింది.",
      analogy: "భారీ వర్షం తర్వాత నీటితో నిండిన తోట నేల లాంటిది.",
      nextSteps: [
        "వెంటనే మీ వైద్యుడిని లేదా కార్డియాలజిస్ట్‌ను సంప్రదించండి.",
        "కాళ్ల వాపు లేదా పడుకున్నప్పుడు శ్వాస తీసుకోవడంలో ఇబ్బంది ఉందేమో గమనించండి.",
        "వైద్యుల సలహా లేకుండా మందులను మార్చవద్దు.",
      ],
      careCategory: "సత్వర వైద్య పరిశీలన",
    },
  },

  Emphysema: {
    clinicalLabel: "Emphysema",
    en: {
      title: "Emphysema (Over-Expanded Lung Air Sacs)",
      badge: "Thoracic Finding • Chronic Lung Changes",
      whatItMeans:
        "The fragile walls between tiny air sacs have broken down, creating larger, less elastic air pockets that trap stale air inside the lungs.",
      whatModelSaw:
        "The model noted signs of lung hyperinflation, flattened diaphragms, or darker-than-normal lung fields with reduced vessel markings.",
      analogy: "Like an overstretched sweater that has lost its bounce and cannot snap back into shape.",
      nextSteps: [
        "Discuss chronic lung health and lung function testing (spirometry) with your doctor.",
        "If you smoke, stopping smoking is the single most effective step to protect your lungs.",
        "Maintain prescribed inhaler routines if already diagnosed with COPD.",
      ],
      careCategory: "Chronic Care Evaluation",
    },
    ta: {
      title: "எம்ஃபிஸிமா (நுரையீரல் காற்றுப் பைகள் சேதமடைதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • நீண்டகால நுரையீரல் மாற்றம்",
      whatItMeans:
        "நுரையீரல் காற்றுப் பைகளின் நுண்ணிய சுவர்கள் சேதமடைந்து நெகிழ்வுத்தன்மையை இழந்து காற்றில் விரிவடைந்துள்ளன.",
      whatModelSaw:
        "நுரையீரல் மிகையாக விரிவடைந்து உதரவிதானம் தட்டையாகியுள்ள மாற்றங்களை கணினி மாதிரி கண்டறிந்துள்ளது.",
      analogy: "நெகிழ்வுத்தன்மையை இழந்து தளர்ந்துபோன பழைய ரப்பர் பேண்ட் போன்ற நிலை.",
      nextSteps: [
        "சுவாச நுரையீரல் பரிசோதனை (Spirometry) குறித்து மருத்துவரிடம் ஆலோசிக்கவும்.",
        "புகைபிடிக்கும் பழக்கம் இருந்தால் உடனடியாக கைவிடுவது நுரையீரலை பாதுகாக்கும்.",
        "மருத்துவர் பரிந்துரைத்த இன்ஹேலர் மருந்துகளை தொடர்ந்து பயன்படுத்தவும்.",
      ],
      careCategory: "நீண்டகால சுவாசப் பராமரிப்பு",
    },
    hi: {
      title: "वातस्फीति / एम्फाइसीमा (फेफड़ों की वायु-थैलियों का विस्तार)",
      badge: "वक्षीय निष्कर्ष • दीर्घकालिक फेफड़े का बदलाव",
      whatItMeans:
        "फेफड़ों की वायु-थैलियों की दीवारें कमजोर होकर क्षतिग्रस्त हो गई हैं, जिससे फेफड़ों में पुरानी हवा फंस जाती है।",
      whatModelSaw:
        "मॉडल ने फेफड़ों के अति-विस्तार और सामान्य से अधिक काले दिखने वाले क्षेत्रों का पैटर्न देखा है।",
      analogy: "एक पुराने ढीले रबर बैंड की तरह जो अपनी लचीलापन खो चुका हो।",
      nextSteps: [
        "फेफड़ों की क्षमता परीक्षण (स्पायरोमेट्री) के लिए डॉक्टर से बात करें।",
        "यदि धूम्रपान करते हैं, तो इसे तुरंत बंद करना फेफड़ों के लिए सबसे जरूरी है।",
        "सीओपीडी की निर्धारित दवाएं नियमित रखें।",
      ],
      careCategory: "दीर्घकालिक देखभाल मूल्यांकन",
    },
    te: {
      title: "ఎంఫిసెమా (ఊపిరితిత్తుల గాలి గదులు సాగిపోవడం)",
      badge: "ఛాతీ పరిశీలన • దీర్ఘకాలిక మార్పులు",
      whatItMeans:
        "ఊపిరితిత్తులలోని గాలి గదుల గోడలు దెబ్బతిని సాగిపోవడం వల్ల పాత గాలి లోపలే ఉండిపోతుంది.",
      whatModelSaw:
        "ఊపిరితిత్తులు ఎక్కువగా ఉబ్బినట్లు కనిపించే నమూనాను AI మోడల్ గుర్తించింది.",
      analogy: "సాగదీయబడి తన స్థితిస్థాపకతను కోల్పోయిన పాత రబ్బరు బ్యాండ్ లాంటిది.",
      nextSteps: [
        "ఊపిరితిత్తుల పనితీరు పరీక్ష (స్పైరోమెట్రీ) గురించి వైద్యుడితో మాట్లాడండి.",
        "ధూమపానం చేసే అలవాటు ఉంటే వెంటనే మానేయడం శ్రేయస్కరం.",
        "డాక్టర్ సూచించిన ఇన్హేలర్లను క్రమం తప్పకుండా వాడండి.",
      ],
      careCategory: "దీర్ఘకాలిక సంరక్షణ సమీక్ష",
    },
  },

  Fibrosis: {
    clinicalLabel: "Fibrosis",
    en: {
      title: "Pulmonary Fibrosis (Lung Tissue Scarring)",
      badge: "Thoracic Finding • Interstitial Scarring",
      whatItMeans:
        "Lung tissue has become thickened, stiff, and scarred over time, making it harder for the lungs to expand smoothly and transfer oxygen into the bloodstream.",
      whatModelSaw:
        "The algorithm detected fine linear reticular markings, mesh-like patterns, or reduced lung volumes typical of fibrous tissue.",
      analogy: "Like smooth silk fabric turning into stiff, coarse burlap.",
      nextSteps: [
        "Schedule an evaluation with a pulmonologist (lung specialist).",
        "A high-resolution chest CT scan is usually needed to confirm and characterize lung fibrosis.",
        "Mention any past workplace dust exposures or autoimmune conditions to your doctor.",
      ],
      careCategory: "Specialist Consultation",
    },
    ta: {
      title: "பல்மோனரி ஃபைப்ரோசிஸ் (நுரையீரல் தழும்பு திசு உருவாக்கம்)",
      badge: "மார்பு கண்டுபிடிப்பு • தழும்பு திசு",
      whatItMeans:
        "நுரையீரல் திசுக்கள் கடினமாகவும் தழும்புகளுடனும் மாறி, நுரையீரல் விரிவடைவதையும் பிராணவாயு பரிமாற்றத்தையும் கடினமாக்குகின்றன.",
      whatModelSaw:
        "நுரையீரல் திசுக்களில் வலை போன்ற மெல்லிய தழும்பு வரிகளின் அடர்த்தியை மாதிரி கண்டறிந்துள்ளது.",
      analogy: "மென்மையான பட்டுத் துணி கடினமான சணல் துணியாக மாறுவது போன்றது.",
      nextSteps: [
        "நுரையீரல் சிறப்பு மருத்துவரை (Pulmonologist) அணுகவும்.",
        "துல்லியமான விவரங்களை அறிய மார்பு சிடி ஸ்கேன் (HRCT) தேவைப்படலாம்.",
        "வேலை செய்யும் இடத்தில் தூசு அல்லது ரசாயன பாதிப்பு இருந்ததா என்பதை மருத்துவரிடம் கூறவும்.",
      ],
      careCategory: "சிறப்பு மருத்துவர் ஆலோசனை",
    },
    hi: {
      title: "पल्मोनरी फाइब्रोसिस (फेफड़ों में रेशेदार निशान / स्कारिंग)",
      badge: "वक्षीय निष्कर्ष • फेफड़ों का कड़ापन",
      whatItMeans:
        "फेफड़ों का सामान्य लचीला ऊतक कठोर और रेशेदार हो गया है, जिससे फेफड़े आसानी से फैल नहीं पाते और ऑक्सीजन प्रवाह में बाधा आती है।",
      whatModelSaw:
        "मॉडल ने फेफड़े के ऊतकों में जालीदार (रेटिकुलर) निशानों का पैटर्न देखा है जो स्कारिंग का संकेत हो सकता है।",
      analogy: "मुलायम कपड़े का कड़े टाट या बोरी के कपड़े में बदल जाने जैसा।",
      nextSteps: [
        "फेफड़े के विशेषज्ञ (पल्मोनोलॉजिस्ट) से परामर्श लें।",
        "सटीक पुष्टि के लिए अक्सर हाई-रिज़ॉल्यूशन सीटी स्कैन (HRCT) की आवश्यकता होती है।",
        "धूल या रसायनों के पुराने संपर्क की जानकारी डॉक्टर को दें।",
      ],
      careCategory: "विशेषज्ञ परामर्श अनुशंसित",
    },
    te: {
      title: "పల్మోనరీ ఫైబ్రోసిస్ (ఊపిరితిత్తుల కణజాలం గట్టిపడటం)",
      badge: "ఛాతీ పరిశీలన • కణజాల మచ్చలు",
      whatItMeans:
        "ఊపిరితిత్తుల కణజాలం గట్టిపడి మచ్చలుగా మారడం వల్ల ఆక్సిజన్ రక్తంలోకి చేరడం కష్టమవుతుంది.",
      whatModelSaw:
        "ఊపిరితిత్తులలో గట్టిపడిన నార వంటి నమూనాలను AI గుర్తించింది.",
      analogy: "మృదువైన పట్టు వస్త్రం గట్టి గోనెపట్టాగా మారినట్లు ఉండే పరిస్థితి.",
      nextSteps: [
        "ఊపిరితిత్తుల నిపుణుడిని (పల్మోనాలజిస్ట్) సంప్రదించండి.",
        "ఖచ్చితమైన నిర్ధారణ కోసం HRCT స్కాన్ అవసరం కావచ్చు.",
        "గతంలో దుమ్ము లేదా ధూళి వాతావరణంలో పనిచేసిన వివరాలను వైద్యునికి చెప్పండి.",
      ],
      careCategory: "స్పెషలిస్ట్ సంప్రదింపు",
    },
  },

  Effusion: {
    clinicalLabel: "Effusion",
    en: {
      title: "Pleural Effusion (Fluid Around the Lung)",
      badge: "Thoracic Finding • Pleural Fluid",
      whatItMeans:
        "Excess fluid has pooled in the protective space between the outside of the lung and the inside of the chest wall (the pleural cavity).",
      whatModelSaw:
        "The model observed blunting of the sharp lower corners of the lung fields (costophrenic angles), indicating fluid pooling at the lung base.",
      analogy: "Like water collecting at the bottom of a clear plastic bag around an object inside.",
      nextSteps: [
        "Arrange a clinical examination with your healthcare provider.",
        "Your doctor may request a physical exam and possibly an ultrasound to gauge fluid volume.",
        "Do not ignore symptoms like a dry cough or breathlessness when lying down.",
      ],
      careCategory: "Physician Assessment Advised",
    },
    ta: {
      title: "ப்ளூரல் எஃப்யூஷன் (நுரையீரலைச் சுற்றி நீர் சேருதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • உறை நீர் தேக்கம்",
      whatItMeans:
        "நுரையீரலின் வெளிப்புற உறை இடைவெளியில் அதிகப்படியான நீர் தேங்கியுள்ளது.",
      whatModelSaw:
        "நுரையீரலின் அடிப்பகுதியில் உள்ள கூர்மையான விளிம்புகள் நீரினால் மறைக்கப்பட்டிருக்கும் அமைப்பை மாதிரி கண்டறிந்துள்ளது.",
      analogy: "ஒரு பையின் அடியில் நீர் தங்கி கீழ் பகுதியை நிரப்புவது போன்றது.",
      nextSteps: [
        "மருத்துவரிடம் சென்று நேரடி பரிசோதனை செய்து கொள்ளவும்.",
        "நீரின் அளவை துல்லியமாக அறிய அல்ட்ராசவுண்ட் ஸ்கேன் பரிந்துரைக்கப்படலாம்.",
        "படுக்கும் போது மூச்சுத்திணறல் அல்லது வறட்டு இருமல் இருந்தால் தெரிவிக்கவும்.",
      ],
      careCategory: "மருத்துவ பரிசோதனை பரிந்துரைக்கப்படுகிறது",
    },
    hi: {
      title: "प्लूरल एफ्यूजन (फेफड़ों के चारों ओर पानी भरना)",
      badge: "वक्षीय निष्कर्ष • प्लूरल तरल",
      whatItMeans:
        "फेफड़े और छाती की दीवार के बीच की झिल्ली में अतिरिक्त तरल जमा हो गया है।",
      whatModelSaw:
        "मॉडल ने फेफड़े के निचले कोनों (कॉस्टोफ्रेनिक एंगल्स) पर पानी के भराव का पैटर्न देखा है।",
      analogy: "प्लास्टिक थैली के तले में पानी जमा होने जैसा।",
      nextSteps: [
        "अपने चिकित्सक से मिलकर छाती की जाँच कराएं।",
        "तरल की मात्रा देखने के लिए डॉक्टर अल्ट्रासाउंड की सलाह दे सकते हैं।",
        "सूखी खांसी या लेटने पर सांस फूलने पर डॉक्टर को बताएं।",
      ],
      careCategory: "चिकित्सकीय मूल्यांकन आवश्यक",
    },
    te: {
      title: "ప్లూరల్ ఎఫ్యూషన్ (ఊపిరితిత్తుల చుట్టూ ద్రవం చేరడం)",
      badge: "ఛాతీ పరిశీలన • ఊపిరితిత్తుల పొరలో నీరు",
      whatItMeans:
        "ఊపిరితిత్తుల వెలుపలి పొర మరియు ఛాతీ గోడ మధ్య ఖాళీలో ద్రవం పేరుకుపోయింది.",
      whatModelSaw:
        "ఊపిరితిత్తుల దిగువ మూలల్లో ద్రవం నిల్వ ఉన్న నమూనాను కంప్యూటర్ మోడల్ గుర్తించింది.",
      analogy: "ఒక సంచి అడుగుభాగంలో నీరు చేరినట్లు ఉండే స్థితి.",
      nextSteps: [
        "వెంటనే మీ వైద్యుడిని సంప్రదించి పరీక్ష చేయించుకోండి.",
        "ద్రవం పరిమాణాన్ని తెలుసుకోవడానికి అల్ట్రాసౌండ్ స్కాన్ అవసరం కావచ్చు.",
        "పడుకున్నప్పుడు ఆయాసం ఉంటే వైద్యునికి తెలపండి.",
      ],
      careCategory: "వైద్య పరీక్ష అవసరం",
    },
  },

  Pneumonia: {
    clinicalLabel: "Pneumonia",
    en: {
      title: "Pneumonia (Lung Infection Pattern)",
      badge: "Thoracic Finding • Infection Pattern",
      whatItMeans:
        "An infection (caused by bacteria, viruses, or fungi) has inflamed the air sacs in one or both lungs, which may fill with inflammatory fluid.",
      whatModelSaw:
        "The model detected localized patchy opacities consistent with infectious lung inflammation. Clinical symptoms like fever, cough, and chills are needed to confirm pneumonia.",
      analogy: "Like an infected cut on your skin that has become red, warm, and swollen, but located deep inside the lung sponge.",
      nextSteps: [
        "Seek a prompt clinical evaluation by a medical doctor.",
        "A doctor must review your temperature, oxygen level (pulse oximetry), and lung sounds.",
        "Take prescribed medications exactly as instructed by your physician.",
      ],
      careCategory: "Prompt Clinical Care",
    },
    ta: {
      title: "நிமோனியா (நுரையீரல் தொற்று வடிவம்)",
      badge: "மார்பு கண்டுபிடிப்பு • தொற்று வடிவம்",
      whatItMeans:
        "நுரையீரலில் பாக்டீரியா அல்லது வைரஸ் தொற்றினால் காற்றுப் பைகளில் அழற்சி ஏற்பட்டு சளி அல்லது நீர் நிரம்பியுள்ளது.",
      whatModelSaw:
        "தொற்று அழற்சியைக் குறிக்கும் திட்டுத்திட்டான அடர்த்தியான வெள்ளைக் கோலங்களை மாதிரி கண்டறிந்துள்ளது. காய்ச்சல் மற்றும் இருமல் போன்ற அறிகுறிகளுடன் ஒப்பிட்டு உறுதி செய்ய வேண்டும்.",
      analogy: "தோலில் ஏற்பட்ட காயம் வீங்கி நீர் சுரப்பது போல நுரையீரலில் ஏற்படும் அழற்சி.",
      nextSteps: [
        "உடனடியாக மருத்துவரை சந்தித்து சிகிச்சை பெறவும்.",
        "உடல் வெப்பநிலை, ஆக்சிஜன் அளவு மற்றும் நுரையீரல் ஒலிகளை மருத்துவர் பரிசோதிக்க வேண்டும்.",
        "மருத்துவர் பரிந்துரைக்கும் மருந்துகளை முழுமையாக உட்கொள்ளவும்.",
      ],
      careCategory: "விரைவான மருத்துவ சிகிச்சை தேவை",
    },
    hi: {
      title: "निमोनिया (फेफड़ों के संक्रमण का पैटर्न)",
      badge: "वक्षीय निष्कर्ष • संक्रमण पैटर्न",
      whatItMeans:
        "जीवाणु (बैक्टीरिया) या वायरस के कारण फेफड़ों में संक्रमण हो गया है, जिससे वायु-थैलियों में सूजन और तरल आ गया है।",
      whatModelSaw:
        "मॉडल ने फेफड़ों में संक्रमण के अनुकूल धब्बेदार घनत्व देखा है। बुखार और खांसी के लक्षणों के आधार पर डॉक्टर इसकी पुष्टि करेंगे।",
      analogy: "त्वचा पर आई किसी सूजन और संक्रमण जैसी स्थिति, जो फेफड़ों के अंदर हो।",
      nextSteps: [
        "बिना देर किए डॉक्टर से परामर्श लें।",
        "डॉक्टर तापमान, ऑक्सीजन स्तर और फेफड़ों की आवाज़ की जाँच करेंगे।",
        "निर्धारित दवाओं का कोर्स पूरा करें।",
      ],
      careCategory: "शीघ्र चिकित्सीय उपचार",
    },
    te: {
      title: "న్యుమోనియా (ఊపిరితిత్తుల ఇన్ఫెక్షన్ నమూనా)",
      badge: "ఛాతీ పరిశీలన • ఇన్ఫెక్షన్ నమూనా",
      whatItMeans:
        "బ్యాక్టీరియా లేదా వైరస్ వల్ల ఊపిరితిత్తులలో ఇన్ఫెక్షన్ వచ్చి గాలి గదులు వాపుతో కూడిన ద్రవంతో నిండాయి.",
      whatModelSaw:
        "ఇన్ఫెక్షన్ వల్ల వచ్చే మచ్చల నమూనాను AI గుర్తించింది. జ్వరం, దగ్గు లక్షణాలతో కలిపి వైద్యులు నిర్ధారించాలి.",
      analogy: "చర్మంలో వాపు వచ్చినట్లుగా ఊపిరితిత్తుల లోపల ఏర్పడే ఇన్ఫెక్షన్ పరిస్థితి.",
      nextSteps: [
        "వెంటనే వైద్యుడిని సంప్రదించి పరీక్ష చేయించుకోండి.",
        "శరీర ఉష్ణోగ్రత, ఆక్సిజన్ స్థాయిలను వైద్యులు పరిశీలిస్తారు.",
        "డాక్టర్ సూచించిన మందులను సమయానికి వాడండి.",
      ],
      careCategory: "సత్వర వైద్య సంరక్షణ",
    },
  },

  Pleural_Thickening: {
    clinicalLabel: "Pleural_Thickening",
    en: {
      title: "Pleural Thickening (Thickened Lung Lining)",
      badge: "Thoracic Finding • Pleural Scar Tissue",
      whatItMeans:
        "The thin protective membrane surrounding your lungs (the pleura) has become thicker than normal, often from past infection, inflammation, or healed pleurisy.",
      whatModelSaw:
        "The model observed an area of thickened border along the edge of the chest wall or lung apices. This is commonly an old, inactive scar.",
      analogy: "Like a tough callus forming on the skin after repeated friction or an old scrape.",
      nextSteps: [
        "Mention any past chest infections, surgeries, or dust exposures to your physician.",
        "Most stable pleural scars require no specific treatment, but baseline tracking is helpful.",
        "Consult your doctor for comparison with prior chest X-rays if available.",
      ],
      careCategory: "Routine Medical Review",
    },
    ta: {
      title: "ப்ளூரல் தடிமன் (நுரையீரல் உறை தடித்தல்)",
      badge: "மார்பு கண்டுபிடிப்பு • உறை தழும்பு",
      whatItMeans:
        "நுரையீரலை மூடியுள்ள மெல்லிய உறை முந்தைய தொற்று அல்லது அழற்சியின் காரணமாக தடித்துப் போயுள்ளது.",
      whatModelSaw:
        "மார்பு கூட்டின் விளிம்பில் உறை தடித்திருப்பதற்கான நிழல் அமைப்பை மாதிரி கவனித்துள்ளது. இது பெரும்பாலும் பழைய ஆறிய தழும்பாகும்.",
      analogy: "பழைய காயம் ஆறிய பிறகு தோலில் ஏற்படும் தடித்த தழும்பு போன்றது.",
      nextSteps: [
        "கடந்த கால மார்பு தொற்று அல்லது அறுவை சிகிச்சை பற்றி மருத்துவரிடம் கூறவும்.",
        "பழைய தழும்புகளுக்கு பொதுவாக தீவிர சிகிச்சை தேவைப்படுவதில்லை.",
        "முந்தைய எக்ஸ்-ரே படங்கள் இருந்தால் மருத்துவரிடம் ஒப்பிட்டுப் பார்க்கவும்.",
      ],
      careCategory: "வழக்கமான மருத்துவ ஆய்வு",
    },
    hi: {
      title: "प्लूरल थिकनिंग (फेफड़े की झिल्ली का मोटा होना)",
      badge: "वक्षीय निष्कर्ष • प्लूरल निशान",
      whatItMeans:
        "फेफड़े को ढकने वाली पतली झिल्ली (प्लूरा) पुराने संक्रमण या सूजन के कारण सामान्य से मोटी हो गई है।",
      whatModelSaw:
        "मॉडल ने छाती की दीवार के किनारे झिल्ली के मोटे होने का पैटर्न देखा है, जो अक्सर पुराना सूखा हुआ निशान होता है।",
      analogy: "पुरानी चोट के बाद त्वचा पर बने सख्त निशान (कैलस) की तरह।",
      nextSteps: [
        "पुराने संक्रमण या धूल के संपर्क की जानकारी डॉक्टर को दें।",
        "पुराने स्थिर निशानों के लिए आमतौर पर किसी विशेष इलाज की आवश्यकता नहीं होती।",
        "यदि पुराने एक्स-रे उपलब्ध हों तो डॉक्टर से तुलना कराएं।",
      ],
      careCategory: "सामान्य चिकित्सीय समीक्षा",
    },
    te: {
      title: "ప్లూరల్ మందగించడం (ఊపిరితిత్తుల పొర మందం కావడం)",
      badge: "ఛాతీ పరిశీలన • పొరపై మచ్చ",
      whatItMeans:
        "ఊపిరితిత్తులను కప్పి ఉంచే పలచటి పొర గతంలో వచ్చిన ఇన్ఫెక్షన్ లేదా వాపు కారణంగా మందంగా మారింది.",
      whatModelSaw:
        "ఛాతీ అంచులలో పొర మందంగా మారిన నమూనాను కంప్యూటర్ గుర్తించింది. ఇది సాధారణంగా పాత మచ్చ కావచ్చు.",
      analogy: "పాత గాయం నయమైన తర్వాత చర్మంపై ఏర్పడే గట్టి మచ్చ లాంటిది.",
      nextSteps: [
        "గతంలో వచ్చిన ఛాతీ ఇన్ఫెక్షన్ల వివరాలను వైద్యునికి చెప్పండి.",
        "పాత మచ్చలకు సాధారణంగా ప్రత్యేక చికిత్స అవసరం ఉండదు.",
        "పాత ఎక్స్-రేలతో పోల్చడానికి వైద్యుడికి చూపించండి.",
      ],
      careCategory: "సాధారణ వైద్య సమీక్ష",
    },
  },

  Cardiomegaly: {
    clinicalLabel: "Cardiomegaly",
    en: {
      title: "Cardiomegaly (Enlarged Heart Silhouette)",
      badge: "Thoracic Finding • Cardiac Silhouette",
      whatItMeans:
        "The shadow of your heart on the radiograph appears wider than half the total width of your chest cavity, suggesting an enlarged heart silhouette.",
      whatModelSaw:
        "The algorithm calculated a cardiothoracic ratio exceeding normal limits (> 50%). Shallow inspiration or portable projection can also falsely widen this shadow.",
      analogy: "Like a person casting a wider shadow depending on the light angle, or a pump that has grown bulkier from working against pressure.",
      nextSteps: [
        "Have your blood pressure checked by a doctor.",
        "An echocardiogram (heart ultrasound) is the gold standard test to measure true heart size.",
        "Do not panic: an apparent enlargement on X-ray is often due to posture or deep breath depth.",
      ],
      careCategory: "Cardiovascular Evaluation",
    },
    ta: {
      title: "கார்டியோமெகலி (இதய நிழல் பெரிதாகக் காணப்படுதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • இதய நிழல்",
      whatItMeans:
        "எக்ஸ்-ரே படத்தில் இதயத்தின் நிழல் மார்பு அகலத்தில் பாதிக்கும் மேல் அகலமாகத் தெரிகிறது.",
      whatModelSaw:
        "இதயத்திற்கும் மார்புக்கும் இடையேயான விகிதம் (Cardiothoracic Ratio) அதிகமாக உள்ளதை மாதிரி கண்டறிந்துள்ளது. மூச்சை குறைவாக இழுத்திருந்தாலும் இப்படி நிழல் பெரிதாகத் தெரியலாம்.",
      analogy: "அதிக அழுத்தத்திற்கு எதிராக வேலை செய்வதால் பெரிதான மோட்டார் போன்றது.",
      nextSteps: [
        "உங்கள் மருத்துவரிடம் இரத்த அழுத்தத்தை பரிசோதித்துக் கொள்ளவும்.",
        "இதயத்தின் உண்மையான அளவை அறிய எக்கோ கார்டியோகிராம் (Echocardiogram) பரிசோதனை சிறந்தது.",
        "பதற்றப்பட வேண்டாம்; எக்ஸ்-ரே எடுக்கும் நிலை காரணமாகவும் நிழல் பெரிதாகத் தெரிய வாய்ப்புள்ளது.",
      ],
      careCategory: "இதய நலப் பரிசோதனை தேவை",
    },
    hi: {
      title: "कार्डियोमेगाली (हृदय की छाया का बढ़ा हुआ दिखना)",
      badge: "वक्षीय निष्कर्ष • हृदय का आकार",
      whatItMeans:
        "एक्स-रे पर दिल की परछाई छाती की कुल चौड़ाई के आधे से अधिक चौड़ी दिख रही है।",
      whatModelSaw:
        "मॉडल ने कार्डियोथोरैसिक अनुपात बढ़ा हुआ पाया है। सांस पूरी न भरने पर भी दिल की छाया बड़ी दिख सकती है।",
      analogy: "दबाव में लगातार काम करने से भारी हुई मोटर की तरह।",
      nextSteps: [
        "अपने डॉक्टर से ब्लड प्रेशर की जाँच कराएं।",
        "हृदय के वास्तविक आकार की पुष्टि के लिए इकोकार्डियोग्राम (इको टेस्ट) सबसे सटीक परीक्षण है।",
        "घबराएं नहीं: कभी-कभी एक्स-रे की स्थिति के कारण भी परछाई बड़ी दिखती है।",
      ],
      careCategory: "हृदय स्वास्थ्य मूल्यांकन",
    },
    te: {
      title: "కార్డియోమెగాలీ (గుండె నీడ పెద్దదిగా కనిపించడం)",
      badge: "ఛాతీ పరిశీలన • గుండె పరిమాణం",
      whatItMeans:
        "ఎక్స్-రేలో గుండె నీడ ఛాతీ వెడల్పులో సగానికి కంటే ఎక్కువ వెడల్పుగా కనిపిస్తుంది.",
      whatModelSaw:
        "ఛాతీతో పోలిస్తే గుండె నిష్పత్తి ఎక్కువగా ఉన్నట్లు కంప్యూటర్ గుర్తించింది. పూర్తిగా ఊపిరి పీల్చుకోకపోయినా ఇలా కనిపించవచ్చు.",
      analogy: "ఎక్కువ ఒత్తిడితో పనిచేయడం వల్ల పరిమాణం పెరిగిన పంప్ లాంటిది.",
      nextSteps: [
        "మీ రక్తపోటును (బీపీ) వైద్యుని వద్ద పరీక్షించుకోండి.",
        "గుండె నిజమైన పరిమాణాన్ని తెలుసుకోవడానికి ఎకో పరీక్ష ఉత్తమమైనది.",
        "కంగారు పడవద్దు; ఫోటో తీసిన కోణం వల్ల కూడా నీడ పెద్దదిగా రావచ్చు.",
      ],
      careCategory: "గుండె పనితీరు పరిశీలన",
    },
  },

  Nodule: {
    clinicalLabel: "Nodule",
    en: {
      title: "Pulmonary Nodule (Small Round Spot ≤ 3 cm)",
      badge: "Thoracic Finding • Focal Nodule",
      whatItMeans:
        "A small, well-defined round or oval spot (up to 3 centimeters across) was noted in the lung tissue. The vast majority of small nodules are benign old scars or healed infections.",
      whatModelSaw:
        "The model flagged a localized circular density. High-resolution CT imaging is required to characterize the shape, edges, and calcification of any suspected nodule.",
      analogy: "Like a small freckle or pebble on an otherwise smooth surface.",
      nextSteps: [
        "Show this result to your doctor for comparison with any past chest imaging.",
        "Stable nodules unchanged over 2 or more years are almost always completely harmless.",
        "Your doctor may recommend a low-dose chest CT scan to verify if a real nodule is present.",
      ],
      careCategory: "Follow-Up Comparison",
    },
    ta: {
      title: "நுரையீரல் நாடியூல் (சிறிய வட்ட வடிவ புள்ளி ≤ 3 செ.மீ)",
      badge: "மார்பு கண்டுபிடிப்பு • சிறிய புள்ளி",
      whatItMeans:
        "நுரையீரலில் 3 செ.மீட்டருக்கும் குறைவான சிறிய வட்ட வடிவ புள்ளி காணப்படுகிறது. இவற்றில் பெரும்பாலானவை ஆபத்தற்ற பழைய தொற்றுத் தழும்புகளே.",
      whatModelSaw:
        "கணினி மாதிரி சிறிய வட்ட வடிவ அடர்த்தியான புள்ளியை கவனித்துள்ளது. இதை உறுதிப்படுத்த மார்பு சிடி ஸ்கேன் தேவைப்படலாம்.",
      analogy: "தோலில் இருக்கும் சிறிய மச்சம் போன்ற பழைய ஆறிய தழும்பு.",
      nextSteps: [
        "பழைய எக்ஸ்-ரேக்கள் இருந்தால் அதனுடன் ஒப்பிட்டுப் பார்க்க மருத்துவரிடம் காண்பிக்கவும்.",
        "இரண்டு வருடங்களுக்கு மேல் மாறாமல் இருக்கும் புள்ளிகள் ஆபத்தற்றவை.",
        "தேவைப்பட்டால் மருத்துவர் சிடி ஸ்கேன் பரிசோதனை செய்ய பரிந்துரைப்பார்.",
      ],
      careCategory: "மருத்துவ ஒப்பீட்டுப் பரிசோதனை",
    },
    hi: {
      title: "पल्मोनरी नोड्यूल (फेफड़े में छोटा गोल धब्बा ≤ 3 सेमी)",
      badge: "वक्षीय निष्कर्ष • छोटा धब्बा",
      whatItMeans:
        "फेफड़े में एक छोटा, गोल या अंडाकार धब्बा (3 सेमी से कम) देखा गया है। अधिकांश छोटे नोड्यूल पुराने संक्रमण के हानिरहित निशान होते हैं।",
      whatModelSaw:
        "मॉडल ने एक छोटा गोल घनत्व पहचाना है। इसकी सटीक पुष्टि के लिए सीटी स्कैन आवश्यक होता है।",
      analogy: "त्वचा पर किसी छोटे तिल या पुराने निशान की तरह।",
      nextSteps: [
        "पुराने एक्स-रे से तुलना कराने के लिए अपने चिकित्सक से मिलें।",
        "यदि यह निशान वर्षों से स्थिर है, तो यह आमतौर पर पूरी तरह सुरक्षित होता है।",
        "डॉक्टर पुष्टि के लिए कम खुराक वाले सीटी स्कैन की सलाह दे सकते हैं।",
      ],
      careCategory: "अनुवर्ती जाँच अनुशंसित",
    },
    te: {
      title: "ఊపిరితిత్తుల నాడ్యూల్ (చిన్న గుండ్రని మచ్చ ≤ 3 సెం.మీ)",
      badge: "ఛాతీ పరిశీలన • చిన్న మచ్చ",
      whatItMeans:
        "ఊపిరితిత్తులలో 3 సెం.మీ కంటే తక్కువ పరిమాణంలో ఒక చిన్న గుండ్రని మచ్చ కనిపించింది. వీటిలో చాలావరకు పాత ఇన్ఫెక్షన్ల వల్ల ఏర్పడిన ప్రమాదకరం కాని మచ్చలే.",
      whatModelSaw:
        "కంప్యూటర్ చిన్న గుండ్రని నమూనాను గుర్తించింది. దీనిని నిర్ధారించడానికి సిటీ స్కాన్ అవసరం కావచ్చు.",
      analogy: "చర్మంపై ఉండే చిన్న పుట్టుమచ్చ లాంటి పాత మచ్చ.",
      nextSteps: [
        "పాత ఎక్స్-రేలతో పోల్చడానికి మీ వైద్యుడికి చూపించండి.",
        "చాలా కాలంగా మార్పు లేకుండా ఉన్న మచ్చలు సాధారణంగా హానికరం కావు.",
        "అవసరమైతే వైద్యులు సిటీ స్కాన్ పరీక్షను సూచిస్తారు.",
      ],
      careCategory: "వైద్య ఫాలో-అప్ అవసరం",
    },
  },

  Mass: {
    clinicalLabel: "Mass",
    en: {
      title: "Thoracic Mass (Larger Dense Region > 3 cm)",
      badge: "Thoracic Finding • Larger Opacity",
      whatItMeans:
        "A denser region larger than 3 centimeters across was identified. This could represent a cyst, abscess, vascular lesion, compact pneumonia, or other growth requiring structured medical investigation.",
      whatModelSaw:
        "The network detected a prominent area of expanded density. An AI model cannot determine whether a mass is benign or malignant from a 2D radiograph.",
      analogy: "Like an opaque cloud on an otherwise clear blue sky that warrants closer inspection.",
      nextSteps: [
        "Schedule an urgent clinical evaluation with your doctor or pulmonologist.",
        "A contrast-enhanced chest CT scan is essential to visualize internal composition.",
        "Do not jump to conclusions: many benign conditions produce mass-like densities on X-rays.",
      ],
      careCategory: "Urgent Specialist Consultation",
    },
    ta: {
      title: "மார்பு கட்டி / மாஸ் (பெரிய அடர்த்தி பகுதி > 3 செ.மீ)",
      badge: "மார்பு கண்டுபிடிப்பு • பெரிய அடர்த்தி",
      whatItMeans:
        "மார்பு பகுதியில் 3 செ.மீட்டருக்கும் அதிகமான பெரிய அடர்த்தியான நிழல் காணப்படுகிறது. இது நீர்க்கட்டி, கடுமையான தொற்று அல்லது திசு வளர்ச்சியாக இருக்கலாம்.",
      whatModelSaw:
        "கணினி மாதிரி பெரிய அடர்த்தியான பகுதியை கண்டறிந்துள்ளது. இரு பரிமாண எக்ஸ்-ரே மூலம் இது ஆபத்தானதா இல்லையா என்பதை AI ஆல் தீர்மானிக்க முடியாது.",
      analogy: "வானில் திடீரென தோன்றும் அடர்ந்த மேகம் போல விரிவான ஆய்வு தேவைப்படும் பகுதி.",
      nextSteps: [
        "உடனடியாக நுரையீரல் சிறப்பு மருத்துவரை அணுகவும்.",
        "கட்டியின் தன்மையை அறிய கான்ட்ராஸ்ட் சிடி ஸ்கேன் (Chest CT) மிகவும் அவசியம்.",
        "பதற்றமடைய வேண்டாம்; பல ஆபத்தற்ற காரணங்களாலும் இத்தகைய தோற்றம் வரலாம்.",
      ],
      careCategory: "விரைவான சிறப்பு மருத்துவர் பரிசோதனை",
    },
    hi: {
      title: "वक्षीय गांठ / मास (3 सेमी से बड़ा सघन क्षेत्र)",
      badge: "वक्षीय निष्कर्ष • बड़ा सघन क्षेत्र",
      whatItMeans:
        "फेफड़े में 3 सेमी से बड़ा एक सघन क्षेत्र देखा गया है। यह सिस्ट, पुराना फोड़ा, गंभीर संक्रमण या कोई अन्य वृद्धि हो सकती है।",
      whatModelSaw:
        "मॉडल ने एक बड़ा सघन क्षेत्र पहचाना है। 2D एक्स-रे से एआई यह तय नहीं कर सकता कि यह हानिरहित है या गंभीर।",
      analogy: "साफ आसमान में दिखे बड़े घने बादल की तरह, जिसकी विस्तृत जाँच जरूरी है।",
      nextSteps: [
        "शीघ्र पल्मोनोलॉजिस्ट (फेफड़े के विशेषज्ञ) से परामर्श लें।",
        "इसकी आंतरिक संरचना समझने के लिए सीटी स्कैन अनिवार्य है।",
        "घबराएं नहीं: कई हानिरहित स्थितियां भी एक्स-रे पर गांठ जैसी दिख सकती हैं।",
      ],
      careCategory: "तत्काल विशेषज्ञ परामर्श",
    },
    te: {
      title: "థొరాసిక్ మాస్ (3 సెం.మీ కంటే పెద్ద గడ్డ)",
      badge: "ఛాతీ పరిశీలన • పెద్ద దట్టమైన ప్రాంతం",
      whatItMeans:
        "ఛాతీలో 3 సెం.మీ కంటే పెద్దదైన దట్టమైన నీడ కనిపించింది. ఇది ఇన్ఫెక్షన్, తిత్తి లేదా ఇతర కణజాల పెరుగుదల కావచ్చు.",
      whatModelSaw:
        "AI మోడల్ ఒక పెద్ద దట్టమైన ప్రాంతాన్ని గుర్తించింది. 2D ఎక్స్-రే ద్వారా ఇది ప్రమాదకరమా కాదా అని AI తేల్చలేదు.",
      analogy: "వివరంగా పరిశీలించాల్సిన దట్టమైన ఆకాశ మేఘం లాంటిది.",
      nextSteps: [
        "వెంటనే పల్మోనాలజిస్ట్ (ఊపిరితిత్తుల నిపుణుడిని) సంప్రదించండి.",
        "ఖచ్చితమైన పరిశీలన కోసం ఛాతీ సిటీ స్కాన్ పరీక్ష అవసరం.",
        "ఆందోళన చెందవద్దు; అనేక సాధారణ సమస్యల వల్ల కూడా ఇలా కనిపించవచ్చు.",
      ],
      careCategory: "త్వరిత స్పెషలిస్ట్ పరిశీలన",
    },
  },

  Hernia: {
    clinicalLabel: "Hernia",
    en: {
      title: "Hiatal / Diaphragmatic Hernia",
      badge: "Thoracic Finding • Diaphragmatic Hernia",
      whatItMeans:
        "An abdominal organ (usually part of the stomach) has pushed upward through an opening in the diaphragm muscle into the lower chest cavity.",
      whatModelSaw:
        "The model noticed a gas-and-fluid bubble behind or adjacent to the heart silhouette, typical of a stomach protrusion through the hiatus.",
      analogy: "Like a pocket inside a jacket bulging through a small gap in the lining.",
      nextSteps: [
        "Discuss acid reflux, heartburn, or indigestion symptoms with your doctor.",
        "Eating smaller meals and avoiding lying down immediately after eating can ease symptoms.",
        "Your doctor can determine if any gastrointestinal imaging is warranted.",
      ],
      careCategory: "Gastroenterology / Primary Care",
    },
    ta: {
      title: "ஹெர்னியா (உதரவிதான குடலிறக்கம் / இரைப்பை நகர்வு)",
      badge: "மார்பு கண்டுபிடிப்பு • உதரவிதான குடலிறக்கம்",
      whatItMeans:
        "வயிற்றுப்பகுதியில் இருக்க வேண்டிய இரைப்பையின் ஒரு பகுதி உதரவிதான தசை வழியாக மார்புப் பகுதிக்குள் மேல்நோக்கி நகர்ந்துள்ளது.",
      whatModelSaw:
        "இதயத்தின் பின்புறத்தில் காற்று அல்லது திரவ குமிழி தோற்றத்தை மாதிரி கவனித்துள்ளது.",
      analogy: "உடையின் சிறிய துளை வழியாக உள்ளாடை லேசாக வெளித்தள்ளுவது போன்ற நிலை.",
      nextSteps: [
        "நெஞ்செரிச்சல், அசிடிட்டி அல்லது செரிமானக் கோளாறு இருந்தால் மருத்துவரிடம் தெரிவிக்கவும்.",
        "சிறிய அளவிலான உணவை உண்பதும், உண்ட உடனே படுக்காமல் இருப்பதும் நல்லது.",
        "தேவைப்பட்டால் இரைப்பை குடல் நிபுணரை அணுகவும்.",
      ],
      careCategory: "செரிமான நல மருத்துவர் ஆலோசனை",
    },
    hi: {
      title: "हर्निया (डायाफ्रामेटिक / हाइटल हर्निया)",
      badge: "वक्षीय निष्कर्ष • डायाफ्राम हर्निया",
      whatItMeans:
        "पेट का एक हिस्सा (आमतौर पर आमाशय) डायाफ्राम की मांसपेशी के छेद से होकर छाती के निचले हिस्से में खिसक गया है।",
      whatModelSaw:
        "मॉडल ने हृदय की छाया के पीछे गैस या तरल का बुलबुला देखा है जो हर्निया का सामान्य संकेत है।",
      analogy: "कपड़े के छोटे छेद से अंदरूनी अस्तर के बाहर उभरने जैसा।",
      nextSteps: [
        "एसिडिटी, सीने में जलन या खट्टी डकार के बारे में डॉक्टर से बात करें।",
        "कम मात्रा में भोजन करें और खाने के तुरंत बाद न लेटें।",
        "गैस्ट्रोएंटेरोलॉजिस्ट से परामर्श ले सकते हैं।",
      ],
      careCategory: "पेट व पाचन विशेषज्ञ परामर्श",
    },
    te: {
      title: "హెర్నియా (డయాఫ్రాగ్రామాటిక్ హెర్నియా)",
      badge: "ఛాతీ పరిశీలన • కడుపు పైకి జారడం",
      whatItMeans:
        "కడుపులోని భాగం (జీర్ణాశయం) డయాఫ్రాగమ్ కండరం గుండా ఛాతీ కింది భాగంలోకి పైకి చొచ్చుకు వచ్చింది.",
      whatModelSaw:
        "గుండె వెనుక భాగంలో గాలి లేదా ద్రవ బుడగ వంటి నమూనాను మోడల్ గుర్తించింది.",
      analogy: "చిన్న రంధ్రం గుండా లోపలి భాగం పైకి ఉబ్బినట్లు ఉండే పరిస్థితి.",
      nextSteps: [
        "ఎసిడిటీ, ఛాతీలో మంట లేదా అజీర్తి లక్షణాల గురించి వైద్యుడితో మాట్లాడండి.",
        "కొద్దికొద్దిగా ఆహారం తీసుకోవడం, తిన్న వెంటనే పడుకోకపోవడం మంచిది.",
        "అవసరమైతే గ్యాస్ట్రోఎంటరాలజిస్ట్‌ను సంప్రదించండి.",
      ],
      careCategory: "జీర్ణకోశ నిపుణుడి సంప్రదింపు",
    },
  },

  "Lung Lesion": {
    clinicalLabel: "Lung Lesion",
    en: {
      title: "Lung Lesion (Localized Area of Tissue Alteration)",
      badge: "Thoracic Finding • Tissue Lesion",
      whatItMeans:
        "A localized patch of altered lung tissue was flagged. 'Lesion' is a general medical term for any abnormal spot, scar, infection focus, or tissue growth.",
      whatModelSaw:
        "The model observed an area differing from normal healthy lung texture. It cannot diagnose the exact tissue type from a standard X-ray.",
      analogy: "Like a mark on a wall that could be an old pencil scuff, patch of putty, or real crack.",
      nextSteps: [
        "Schedule a follow-up review with your healthcare provider.",
        "Bring any prior X-rays or scans for comparison to determine if this lesion is new or old.",
        "Your doctor will guide you on whether further imaging (like CT) is helpful.",
      ],
      careCategory: "Physician Review Advised",
    },
    ta: {
      title: "நுரையீரல் புண் / காயம் (நுரையீரல் திசு மாற்றம்)",
      badge: "மார்பு கண்டுபிடிப்பு • திசு காயம்",
      whatItMeans:
        "நுரையீரல் திசுவில் ஒரு குறிப்பிட்ட பகுதியில் மாற்றம் காணப்படுகிறது. 'Lesion' என்பது காயம், தழும்பு அல்லது பழைய தொற்றைக் குறிக்கும் பொதுவான சொல்.",
      whatModelSaw:
        "சாதாரண நுரையீரல் அமைப்பிலிருந்து மாறுபட்ட அடர்த்தி புள்ளியை மாதிரி கவனித்துள்ளது.",
      analogy: "சுவரில் இருக்கும் சிறிய கறை போன்றது; அது பழைய கறையா அல்லது புதிய விரிசலா என ஆராய வேண்டும்.",
      nextSteps: [
        "உங்கள் மருத்துவரிடம் ஆலோசனை பெறவும்.",
        "இது புதியதா அல்லது பழையதா என அறிய முந்தைய ஸ்கேன்களுடன் ஒப்பிடவும்.",
        "தேவைப்பட்டால் கூடுதல் சிடி ஸ்கேன் பரிசோதனை செய்யப்படலாம்.",
      ],
      careCategory: "மருத்துவ ஆய்வு பரிந்துரைக்கப்படுகிறது",
    },
    hi: {
      title: "फेफड़े का घाव / घाव का निशान (टिशू घाव)",
      badge: "वक्षीय निष्कर्ष • असामान्य ऊतक",
      whatItMeans:
        "फेफड़े के ऊतक में एक असामान्य धब्बा देखा गया है। 'लीजन' किसी भी पुराने घाव, निशान या संक्रमण के लिए एक सामान्य चिकित्सीय शब्द है।",
      whatModelSaw:
        "मॉडल ने सामान्य फेफड़े से भिन्न ऊतक घनत्व देखा है। यह सीधे तौर पर किसी बीमारी की पुष्टि नहीं करता।",
      analogy: "दीवार पर बने किसी धब्बे की तरह, जिसे करीब से देखने की जरूरत है।",
      nextSteps: [
        "अपने डॉक्टर से मिलकर इस परिणाम की समीक्षा कराएं।",
        "पुराने एक्स-रे से तुलना कराकर देखें कि यह पुराना है या नया।",
        "डॉक्टर की सलाह से आवश्यक होने पर सीटी स्कैन कराएं।",
      ],
      careCategory: "चिकित्सकीय समीक्षा अनुशंसित",
    },
    te: {
      title: "ఊపిరితిత్తుల గాయం / మచ్చ (కణజాల మార్పు)",
      badge: "ఛాతీ పరిశీలన • అసాధారణ కణజాలం",
      whatItMeans:
        "ఊపిరితిత్తుల కణజాలంలో ఒక ప్రత్యేక భాగంలో మార్పు కనిపించింది. ఇది పాత ఇన్ఫెక్షన్ లేదా మచ్చ కావచ్చు.",
      whatModelSaw:
        "సాధారణ ఊపిరితిత్తుల కంటే భిన్నమైన నమూనాను AI గుర్తించింది.",
      analogy: "గోడపై ఉన్న గుర్తు లాంటిది; అది పాత మచ్చా లేదా కొత్త పగులా అని చూడాలి.",
      nextSteps: [
        "మీ వైద్యుడిని సంప్రదించి సలహా తీసుకోండి.",
        "ఇది పాతదా కొత్తదా తెలుసుకోవడానికి పాత స్కాన్‌లతో పోల్చండి.",
        "అవసరమైతే తదుపరి పరీక్షల కోసం డాక్టర్ మార్గదర్శకత్వం తీసుకోండి.",
      ],
      careCategory: "వైద్య సమీక్ష సిఫార్సు చేయబడింది",
    },
  },

  Fracture: {
    clinicalLabel: "Fracture",
    en: {
      title: "Rib / Thoracic Bone Fracture",
      badge: "Thoracic Finding • Bone Discontinuity",
      whatItMeans:
        "A break, crack, or discontinuity was flagged in one of the bones visible on the chest radiograph (such as ribs, collarbone, or thoracic vertebrae).",
      whatModelSaw:
        "The model detected an interruption in bone cortical continuity. Healing callus from an old fracture can also produce this appearance.",
      analogy: "Like a hairline crack in a ceramic plate or a repaired branch with an old knobby mend.",
      nextSteps: [
        "Tell your doctor if you recently had a fall, chest trauma, or severe coughing spells.",
        "Your doctor may palpate your ribs to identify any localized tenderness.",
        "Most uncomplicated rib cracks heal with rest, ice, and pain management over 6 to 8 weeks.",
      ],
      careCategory: "Orthopedic / Medical Review",
    },
    ta: {
      title: "விலா எலும்பு முறிவு / விரிசல்",
      badge: "மார்பு கண்டுபிடிப்பு • எலும்பு விரிசல்",
      whatItMeans:
        "மார்பு எக்ஸ்-ரேயில் தெரியும் விலா எலும்பு அல்லது காறை எலும்பில் விரிசல் அல்லது முறிவு தென்படுகிறது.",
      whatModelSaw:
        "எலும்பின் எல்லையில் விரிசல் அல்லது பழைய எலும்பு ஆறும் தழும்பின் அமைப்பை மாதிரி கண்டறிந்துள்ளது.",
      analogy: "பீங்கான் தட்டில் ஏற்பட்ட சிறிய விரிசல் போன்றது.",
      nextSteps: [
        "சமீபத்தில் கீழே விழுந்தீர்களா அல்லது பலத்த இருமல் ஏற்பட்டதா என்பதை மருத்துவரிடம் கூறவும்.",
        "வலியை குறைக்க ஓய்வு மற்றும் தகுந்த மருந்துகளை மருத்துவர் பரிந்துரைப்பார்.",
        "எளிய விலா எலும்பு விரிசல்கள் 6 முதல் 8 வாரங்களில் ஓய்வில் குணமாகும்.",
      ],
      careCategory: "எலும்பு நல மருத்துவர் ஆலோசனை",
    },
    hi: {
      title: "पसली या छाती की हड्डी में फ्रैक्चर / दरार",
      badge: "वक्षीय निष्कर्ष • हड्डी में दरार",
      whatItMeans:
        "एक्स-रे में दिखने वाली पसली, कॉलर की हड्डी या रीढ़ की हड्डी में दरार या टूटन का संकेत है।",
      whatModelSaw:
        "मॉडल ने हड्डी की रूपरेखा में रुकावट देखी है। पुरानी जुड़ चुकी हड्डी का उभार भी ऐसा दिख सकता है।",
      analogy: "चीनी मिट्टी की प्लेट में आई हल्की दरार की तरह।",
      nextSteps: [
        "हाल ही में हुई किसी चोट, गिरने या अत्यधिक खांसी के बारे में डॉक्टर को बताएं।",
        "दर्द और सूजन के लिए डॉक्टर से परामर्श लें।",
        "अधिकांश पसलियों की दरारें 6 से 8 सप्ताह में आराम से ठीक हो जाती हैं।",
      ],
      careCategory: "अस्थि रोग विशेषज्ञ परामर्श",
    },
    te: {
      title: "పక్కటెముక లేదా ఎముక విరుపు / పగులు",
      badge: "ఛాతీ పరిశీలన • ఎముకలో పగులు",
      whatItMeans:
        "ఎక్స్-రేలో కనిపించే పక్కటెముక లేదా ఇతర ఎముకలలో పగులు లేదా విరుపు కనిపించింది.",
      whatModelSaw:
        "ఎముక ఆకారంలో అంతరాయం ఉన్నట్లు AI మోడల్ గుర్తించింది. పాత గాయం మానడం వల్ల కూడా ఇలా కనిపించవచ్చు.",
      analogy: "సిరామిక్ ప్లేట్‌లో వచ్చిన చిన్న పగులు లాంటిది.",
      nextSteps: [
        "ఇటీవల పడిపోవడం లేదా తీవ్రమైన దగ్గు వచ్చినట్లయితే వైద్యునికి చెప్పండి.",
        "విశ్రాంతి మరియు నొప్పి నివారణ కోసం డాక్టర్ సలహా తీసుకోండి.",
        "సాధారణంగా పక్కటెముక పగుళ్లు 6 నుండి 8 వారాలలో నయమవుతాయి.",
      ],
      careCategory: "ఎముకల నిపుణుడి సంప్రదింపు",
    },
  },

  "Lung Opacity": {
    clinicalLabel: "Lung Opacity",
    en: {
      title: "Lung Opacity (Non-Specific Hazy Density)",
      badge: "Thoracic Finding • Radiographic Opacity",
      whatItMeans:
        "An area of the lung appears less transparent (whiter/cloudier) than normal. 'Opacity' is a descriptive radiological term, not a single disease.",
      whatModelSaw:
        "The model noted a cloudy, light region where X-rays were absorbed more than expected. Fluid, inflammation, atelectasis, or scarring can all create opacities.",
      analogy: "Like looking through a window with a frosted or smudged corner.",
      nextSteps: [
        "A healthcare professional must correlate this opacity with your symptoms and history.",
        "Mention whether you have had a fever, cough, chest pain, or smoking history.",
        "Further evaluation or a follow-up X-ray after treatment may be recommended.",
      ],
      careCategory: "Physician Evaluation Advised",
    },
    ta: {
      title: "நுரையீரல் ஒளிபுகாத் தன்மை / மங்கலான பகுதி (ஒபேசிட்டி)",
      badge: "மார்பு கண்டுபிடிப்பு • மங்கலான பகுதி",
      whatItMeans:
        "நுரையீரலின் ஒரு பகுதி சாதாரணமாக இருப்பதை விட மங்கலாகவும் வெள்ளையாகவும் தெரிகிறது. இது ஒரு குறிப்பிட்ட நோய் அல்ல, ஒரு தோற்ற விவரிப்பு மட்டுமே.",
      whatModelSaw:
        "எக்ஸ்-ரே கதிர்களை அதிகமாக உறிஞ்சும் அடர்த்தியான பகுதியை மாதிரி கவனித்துள்ளது. நீர், சளி, அழற்சி அல்லது தழும்பு போன்றவற்றால் இது ஏற்படலாம்.",
      analogy: "ஜன்னல் கண்ணாடியின் ஒரு மூலையில் பனி படிந்து மங்கலாக இருப்பது போன்றது.",
      nextSteps: [
        "இந்த முடிவை மருத்துவரிடம் காண்பித்து உங்கள் அறிகுறிகளுடன் ஒப்பிட்டுப் பார்க்கவும்.",
        "காய்ச்சல், இருமல் அல்லது சளி உள்ளதா என்பதை மருத்துவரிடம் கூறவும்.",
        "சிகிச்சைக்குப் பிறகு மறுபரிசோதனை எக்ஸ்-ரே எடுக்க மருத்துவர் பரிந்துரைக்கலாம்.",
      ],
      careCategory: "மருத்துவ மதிப்பீடு தேவை",
    },
    hi: {
      title: "फेफड़ों का धुंधलापन / ओपेसिटी",
      badge: "वक्षीय निष्कर्ष • धुंधला क्षेत्र",
      whatItMeans:
        "फेफड़े का एक हिस्सा सामान्य से कम पारदर्शी (सफेद या धुंधला) दिख रहा है। 'ओपेसिटी' केवल एक वर्णनात्मक शब्द है, कोई विशिष्ट बीमारी नहीं।",
      whatModelSaw:
        "मॉडल ने फेफड़े में धुंधलापन देखा है। तरल, सूजन, संक्रमण या पुराना निशान इसके कारण हो सकते हैं।",
      analogy: "कांच की खिड़की के एक कोने पर जमी धुंध की तरह।",
      nextSteps: [
        "अपने चिकित्सक से इस एक्स-रे पर चर्चा करें।",
        "बुखार, खांसी या सीने में दर्द की जानकारी डॉक्टर को दें।",
        "उपचार के बाद फॉलो-अप एक्स-रे कराने की सलाह दी जा सकती है।",
      ],
      careCategory: "चिकित्सकीय मूल्यांकन अनुशंसित",
    },
    te: {
      title: "ఊపిరితిత్తుల మసకబారడం (ఒపాసిటీ)",
      badge: "ఛాతీ పరిశీలన • మసక ప్రాంతం",
      whatItMeans:
        "ఊపిరితిత్తుల భాగం సాధారణం కంటే తక్కువ పారదర్శకంగా (తెల్లగా) కనిపిస్తుంది. ఇది ఒక లక్షణ వివరణ మాత్రమే, వ్యాధి కాదు.",
      whatModelSaw:
        "ఊపిరితిత్తులలో మసకబారిన నమూనాను AI గుర్తించింది. ద్రవం, వాపు లేదా మచ్చల వల్ల ఇది రావచ్చు.",
      analogy: "కిటికీ అద్దం ఒక మూలన మసకబారినట్లు కనిపించే స్థితి.",
      nextSteps: [
        "ఈ ఫలితాన్ని మీ వైద్యుడికి చూపించి పరీక్ష చేయించుకోండి.",
        "జ్వరం, దగ్గు వంటి లక్షణాలు ఉంటే వైద్యునికి తెలపండి.",
        "చికిత్స తర్వాత మళ్లీ ఎక్స్-రే తీయించుకోవాలని డాక్టర్ సూచించవచ్చు.",
      ],
      careCategory: "వైద్య మూల్యాంకనం అవసరం",
    },
  },

  "Enlarged Cardiomediastinum": {
    clinicalLabel: "Enlarged Cardiomediastinum",
    en: {
      title: "Enlarged Cardiomediastinum (Widened Central Chest)",
      badge: "Thoracic Finding • Central Mediastinum",
      whatItMeans:
        "The central compartment of your chest (the mediastinum, housing the heart, aorta, esophagus, and lymph nodes) appears wider than typical on the frontal radiograph.",
      whatModelSaw:
        "The model flagged increased width across the mid-chest shadow. Expiratory breath, body rotation, posture, fat deposition, or vascular dilation frequently cause widening.",
      analogy: "Like a tree trunk casting a broader shadow when viewed from a slightly different perspective.",
      nextSteps: [
        "Consult your doctor for clinical correlation.",
        "A full-inspiration radiograph or contrast chest CT clarifies whether true vascular enlargement exists.",
        "Check your blood pressure and report any swallowing or chest pressure issues.",
      ],
      careCategory: "Clinical Review Recommended",
    },
    ta: {
      title: "கார்டியோமீடியாஸ்டினம் விரிவாக்கம் (மத்திய மார்பு அகலமாதல்)",
      badge: "மார்பு கண்டுபிடிப்பு • மத்திய மார்பு அகலம்",
      whatItMeans:
        "இதயம், பெருந்தமனி மற்றும் உணவுப்பாதை அமைந்துள்ள மார்பின் மையப் பகுதி (Mediastinum) வழக்கத்தை விட அகலமாகத் தெரிகிறது.",
      whatModelSaw:
        "மார்பின் மைய நிழல் அகலமாக உள்ளதை மாதிரி கண்டறிந்துள்ளது. உடல் நிலை, கொழுப்பு அல்லது இரத்தக்குழாய் விரிவடைவதால் இது நிகழலாம்.",
      analogy: "கோண மாறுபாட்டால் மரத்தின் அடிப்பகுதி நிழல் அகலமாகத் தெரிவது போன்றது.",
      nextSteps: [
        "உங்கள் மருத்துவரிடம் ஆலோசனை பெறவும்.",
        "முழுமையாக மூச்சை இழுத்து எடுத்த மறு எக்ஸ்-ரே அல்லது சிடி ஸ்கேன் துல்லியத்தை உறுதி செய்யும்.",
        "இரத்த அழுத்தம் மற்றும் உணவு விழுங்குவதில் சிரமம் உள்ளதா என கவனிக்கவும்.",
      ],
      careCategory: "மருத்துவ ஆய்வு பரிந்துரைக்கப்படுகிறது",
    },
    hi: {
      title: "बढ़ा हुआ कार्डियोमीडियास्टिनम (छाती का मध्य भाग चौड़ा होना)",
      badge: "वक्षीय निष्कर्ष • मध्य वक्षीय चौड़ाई",
      whatItMeans:
        "छाती का मध्य भाग (मीडियास्टिनम, जिसमें दिल और मुख्य रक्त वाहिकाएं होती हैं) एक्स-रे पर सामान्य से अधिक चौड़ा दिख रहा है।",
      whatModelSaw:
        "मॉडल ने मध्य छाती की छाया में बढ़ी हुई चौड़ाई देखी है। सांस पूरी न लेने, शरीर के मुड़ने या वसा के जमाव से भी ऐसा दिख सकता है।",
      analogy: "अलग कोण से देखने पर पेड़ के तने की परछाई चौड़ी दिखने जैसा।",
      nextSteps: [
        "अपने चिकित्सक से इस परिणाम पर परामर्श लें।",
        "पूरी सांस भरकर दोबारा एक्स-रे या सीटी स्कैन कराने से स्थिति स्पष्ट हो सकती है।",
        "ब्लड प्रेशर और निगलने में किसी परेशानी की जानकारी दें।",
      ],
      careCategory: "चिकित्सकीय समीक्षा अनुशंसित",
    },
    te: {
      title: "కార్డియోమీడియాస్టినమ్ పెరగడం (మధ్య ఛాతీ వెడల్పు కావడం)",
      badge: "ఛాతీ పరిశీలన • మధ్య ఛాతీ వెడల్పు",
      whatItMeans:
        "గుండె, ప్రధాన రక్తనాళాలు ఉండే ఛాతీ మధ్య భాగం ఎక్స్-రేలో సాధారణం కంటే వెడల్పుగా కనిపిస్తుంది.",
      whatModelSaw:
        "మధ్య ఛాతీ నీడ వెడల్పుగా ఉన్నట్లు AI గుర్తించింది. సరైన శ్వాస తీసుకోకపోవడం వల్ల కూడా ఇలా కనిపించవచ్చు.",
      analogy: "వేరే కోణం నుండి చూసినప్పుడు చెట్టు నీడ వెడల్పుగా కనిపించినట్లు ఉండే పరిస్థితి.",
      nextSteps: [
        "మీ వైద్యుడిని సంప్రదించి పరీక్ష చేయించుకోండి.",
        "స్పష్టత కోసం సిటీ స్కాన్ లేదా సరైన శ్వాసతో మరలా ఎక్స్-రే అవసరం కావచ్చు.",
        "రక్తపోటు మరియు ఆహారం మింగడంలో ఇబ్బందులు ఉంటే వైద్యునికి తెలపండి.",
      ],
      careCategory: "వైద్య సమీక్ష సిఫార్సు చేయబడింది",
    },
  },
};

// Aliases for keys with underscores or spaces
CXR_PATHOLOGY_EXPLANATIONS["Pleural Thickening"] = CXR_PATHOLOGY_EXPLANATIONS.Pleural_Thickening;
CXR_PATHOLOGY_EXPLANATIONS["Lung_Lesion"] = CXR_PATHOLOGY_EXPLANATIONS["Lung Lesion"];
CXR_PATHOLOGY_EXPLANATIONS["Lung_Opacity"] = CXR_PATHOLOGY_EXPLANATIONS["Lung Opacity"];
CXR_PATHOLOGY_EXPLANATIONS["Enlarged_Cardiomediastinum"] = CXR_PATHOLOGY_EXPLANATIONS["Enlarged Cardiomediastinum"];

/**
 * Grad-CAM visual attention interpretations in all 4 languages.
 */
export const CXR_HEATMAP_EXPLANATIONS = {
  en: {
    title: "Understanding the Grad-CAM Visual Attention Map",
    whatItRepresentsTitle: "What the Colored Heatmap Highlights",
    whatItRepresentsText:
      "The colored highlights show which clusters of pixels in your chest radiograph drew the strongest mathematical attention from the neural network when computing the score for the top finding.",
    colorGuideTitle: "Color Interpretation Guide",
    colorRed: "Red / Orange: Areas that contributed most strongly to the AI model's mathematical output.",
    colorYellowGreen: "Yellow / Green: Regions with moderate mathematical influence.",
    colorBlue: "Blue / Dark: Baseline background areas with minimal influence on the decision.",
    whatItCannotProveTitle: "Critical Limits — What the Heatmap CANNOT Prove",
    limits: [
      "A highlighted region is NOT a confirmed lesion, infection border, or tumor margin.",
      "The AI can easily highlight normal bones (ribs, collarbone), heart borders, wires, or positioning artifacts.",
      "A heatmap cannot distinguish an active ongoing infection from an old healed scar.",
      "Never use a highlighted area independently to diagnose disease or guide medical treatment.",
    ],
    doctorRoleTitle: "Why Human Radiologists Are Irreplaceable",
    doctorRoleText:
      "A licensed radiologist or pulmonologist examines subtle bone and soft tissue densities in 3D clinical context with your symptoms, vital signs, and history. The AI heatmap is an experimental research tool, not a doctor's diagnosis.",
  },
  ta: {
    title: "Grad-CAM கவன வரைபடத்தை புரிந்து கொள்ளுங்கள்",
    whatItRepresentsTitle: "வண்ண கவன வரைபடம் எதை காட்டுகிறது?",
    whatItRepresentsText:
      "கணினி மாதிரி முதன்மை முடிவை கணிக்கும் போது, எக்ஸ்-ரே படத்தில் எந்த பகுதிகள் அதன் கணித முடிவிற்கு அதிக பங்களித்தன என்பதை இந்த வண்ண வரைபடம் காட்டுகிறது.",
    colorGuideTitle: "வண்ண வழிகாட்டி",
    colorRed: "சிவப்பு / ஆரஞ்சு: மாதிரி அதிக கவனம் செலுத்திய முதன்மை பகுதிகள்.",
    colorYellowGreen: "மஞ்சள் / பச்சை: மிதமான கவனம் பெற்ற பகுதிகள்.",
    colorBlue: "நீலம் / இருண்ட பகுதி: குறைந்த தாக்கத்தை ஏற்படுத்திய பின்னணி பகுதிகள்.",
    whatItCannotProveTitle: "முக்கிய வரம்புகள் — வரைபடம் எதை நிரூபிக்காது?",
    limits: [
      "வண்ணமிடப்பட்ட பகுதி ஒரு உண்மையான நோய் புண், கட்டி அல்லது தொற்று எல்லை அல்ல.",
      "விலா எலும்புகள், மருத்துவ கம்பிகள் அல்லது படம் எடுத்த கோண மாறுபாடுகளையும் இது சுட்டிக்காட்டலாம்.",
      "நடப்பில் உள்ள தொற்றுக்கும், பழைய ஆறிய தழும்புக்கும் உள்ள வித்தியாசத்தை இதனால் பிரித்தறிய முடியாது.",
      "இந்த வரைபடத்தை மட்டும் வைத்து எந்தவொரு மருத்துவ முடிவையும் எடுக்கக் கூடாது.",
    ],
    doctorRoleTitle: "மருத்துவ நிபுணரின் நேரடி பரிசோதனை ஏன் அவசியம்?",
    doctorRoleText:
      "கதிரியக்க நிபுணர் மட்டுமே உங்கள் முழு மருத்துவ வரலாறு, அறிகுறிகள் மற்றும் முழு மார்பு அமைப்பையும் ஆய்வு செய்து சரியான முடிவை எடுக்க முடியும். இது ஒரு ஆராய்ச்சி கருவி மட்டுமே.",
  },
  hi: {
    title: "Grad-CAM विजुअल अटेंशन हीटमैप को समझें",
    whatItRepresentsTitle: "रंगीन हीटमैप क्या दर्शाता है?",
    whatItRepresentsText:
      "रंगीन हाइलाइट्स यह दिखाते हैं कि आपके छाती के एक्स-रे में किन पिक्सेल समूहों ने शीर्ष निष्कर्ष के लिए मॉडल के स्कोर को सबसे अधिक प्रभावित किया।",
    colorGuideTitle: "रंग व्याख्या गाइड",
    colorRed: "लाल / नारंगी: वे क्षेत्र जिन्होंने एआई मॉडल का सबसे अधिक ध्यान आकर्षित किया।",
    colorYellowGreen: "पीला / हरा: मध्यम प्रभाव वाले क्षेत्र।",
    colorBlue: "नीला / गहरा भाग: सामान्य पृष्ठभूमि क्षेत्र जिनका स्कोर पर न्यूनतम प्रभाव था।",
    whatItCannotProveTitle: "महत्वपूर्ण सीमाएं — हीटमैप क्या साबित नहीं कर सकता?",
    limits: [
      "हाइलाइट किया गया क्षेत्र कोई पक्का घाव, ट्यूमर या संक्रमण की सीमा नहीं है।",
      "एआई पसलियों, कॉलर बोन, चिकित्सा तारों या छाया के सामान्य अंतरों पर भी ध्यान केंद्रित कर सकता है।",
      "हीटमैप सक्रिय संक्रमण और पुराने ठीक हो चुके निशान में अंतर नहीं कर सकता।",
      "केवल हीटमैप के आधार पर कभी भी कोई चिकित्सीय निर्णय न लें या इलाज शुरू न करें।",
    ],
    doctorRoleTitle: "मानव रेडियोलॉजिस्ट क्यों अपरिहार्य हैं?",
    doctorRoleText:
      "एक योग्य रेडियोलॉजिस्ट आपके संपूर्ण स्वास्थ्य इतिहास, लक्षणों और नैदानिक संदर्भ में एक्स-रे की व्याख्या करता है। एआई हीटमैप केवल एक शोध उपकरण है, डॉक्टर का विकल्प नहीं।",
  },
  te: {
    title: "Grad-CAM విజువల్ అటెన్షన్ హీట్‌మ్యాప్‌ను అర్థం చేసుకోండి",
    whatItRepresentsTitle: "రంగుల హీట్‌మ్యాప్ ఏమి చూపుతుంది?",
    whatItRepresentsText:
      "ఛాతీ ఎక్స్-రేలో కంప్యూటర్ మోడల్ ప్రాథమిక నిర్ధారణను లెక్కించడానికి ఏ భాగాలపై ఎక్కువ శ్రద్ధ పెట్టిందో ఈ రంగుల చిత్రం చూపుతుంది.",
    colorGuideTitle: "రంగుల వివరణ గైడ్",
    colorRed: "ఎరుపు / నారింజ: AI మోడల్ అత్యధిక శ్రద్ధ చూపిన ముఖ్య ప్రాంతాలు.",
    colorYellowGreen: "పసుపు / ఆకుపచ్చ: మోడల్ మధ్యస్థ శ్రద్ధ పెట్టిన ప్రాంతాలు.",
    colorBlue: "నీలం / ముదురు భాగం: స్కోరుపై అతి తక్కువ ప్రభావం చూపిన సాధారణ నేపథ్యం.",
    whatItCannotProveTitle: "ముఖ్యమైన పరిమితులు — హీట్‌మ్యాప్ ఏమి రుజువు చేయలేదు?",
    limits: [
      "రంగు చూపించిన ప్రాంతం ఖచ్చితమైన వ్యాధి కణజాలం లేదా కణితి కాకపోవచ్చు.",
      "పక్కటెముకలు, కాలర్ బోన్స్ లేదా ఫోటో కోణం వల్ల కూడా మోడల్ దృష్టి మారవచ్చు.",
      "ఇది ప్రస్తుత ఇన్ఫెక్షన్‌కు మరియు పాత మచ్చకు తేడాను గుర్తించలేదు.",
      "హీట్‌మ్యాప్ ఆధారంగా ఎటువంటి వైద్య నిర్ణయాలు తీసుకోవద్దు.",
    ],
    doctorRoleTitle: "రేడియాలజిస్ట్ పరిశీలన ఎందుకు అవసరం?",
    doctorRoleText:
      "ఒక నిపుణుడైన వైద్యుడు మాత్రమే మీ పూర్తి ఆరోగ్య చరిత్ర మరియు లక్షణాల ఆధారంగా సరైన నిర్ధారణ చేయగలరు. AI హీట్‌మ్యాప్ కేవలం పరిశోధన నమూనా మాత్రమే.",
  },
};

/**
 * Score and Calibration Explanations in all 4 languages.
 * Clarifies that model scores are uncalibrated sigmoid activations, NOT clinical probabilities.
 */
export const CXR_SCORE_EXPLANATIONS = {
  en: {
    title: "Understanding AI Model Scores (Uncalibrated Activation)",
    scoreMeaning:
      "The percentage shown (e.g., 62.5%) is an uncalibrated mathematical activation score generated by an experimental research neural network. It is NOT an 80% or 62% clinical probability that you have a disease.",
    thresholdMeaning:
      "The operating threshold (typically 50%) is an experimental benchmark line used for software testing, NOT an established clinical diagnostic threshold.",
    cautiousInterpretation:
      "A higher score does not confirm disease, and a lower score does not guarantee normal lungs. Only a licensed physician can make a definitive clinical diagnosis.",
  },
  ta: {
    title: "மாதிரி மதிப்பெண் மற்றும் கணக்கீடு (Uncalibrated Score)",
    scoreMeaning:
      "காட்டப்படும் சதவீதம் (எ.கா. 62.5%) என்பது ஒரு ஆராய்ச்சி கணினி மாதிரியின் கணித மதிப்பீடு மட்டுமே. இது உங்களுக்கு நோய் இருப்பதற்கான 62% மருத்துவ சாத்தியக்கூறு அல்ல.",
    thresholdMeaning:
      "அடிப்படைக் குறியீடு (50%) என்பது மென்பொருள் சோதனைக்கான ஒரு வரம்பு மட்டுமே; இது மருத்துவ நோயறிதல் எல்லை அல்ல.",
    cautiousInterpretation:
      "அதிக மதிப்பெண் நோயை உறுதிப்படுத்தாது; குறைந்த மதிப்பெண் நுரையீரல் ஆரோக்கியத்திற்கு உத்தரவாதம் அளிக்காது. உரிமம் பெற்ற மருத்துவர் மட்டுமே முடிவெடுக்க முடியும்.",
  },
  hi: {
    title: "एआई मॉडल स्कोर और निश्चितता (अनकैलिब्रेटेड स्कोर)",
    scoreMeaning:
      "प्रदर्शित प्रतिशत (जैसे 62.5%) एक प्रयोगात्मक कंप्यूटर मॉडल का गणितीय स्कोर है। यह बीमारी होने की 62% नैदानिक संभावना (प्रोबेबिलिटी) नहीं है।",
    thresholdMeaning:
      "थ्रेशोल्ड सीमा (50%) सॉफ्टवेयर परीक्षण का एक पैमाना है, कोई प्रमाणित डॉक्टरी नैदानिक सीमा नहीं।",
    cautiousInterpretation:
      "उच्च स्कोर बीमारी की पुष्टि नहीं करता, और कम स्कोर स्वस्थ फेफड़ों की गारंटी नहीं देता। केवल डॉक्टर ही सही निर्णय ले सकते हैं।",
  },
  te: {
    title: "AI మోడల్ స్కోరు & ఖచ్చితత్వం (అన్‌కాలిబ్రేటెడ్ స్కోరు)",
    scoreMeaning:
      "ఇక్కడ కనిపించే శాతం (ఉదా. 62.5%) అనేది ప్రయోగాత్మక కంప్యూటర్ మోడల్ లెక్కించిన గణిత స్కోరు మాత్రమే. ఇది మీకు వ్యాధి ఉన్నట్లు 62% సంభావ్యత కాదు.",
    thresholdMeaning:
      "పరిమితి మార్కు (50%) అనేది సాఫ్ట్‌వేర్ పరీక్ష కోసం ఉపయోగించే ప్రమాణం మాత్రమే, వైద్య నిబంధన కాదు.",
    cautiousInterpretation:
      "ఎక్కువ స్కోరు వ్యాధిని నిర్ధారించదు, తక్కువ స్కోరు ఊపిరితిత్తులు ఆరోగ్యంగా ఉన్నాయని హామీ ఇవ్వదు. వైద్యుల పరీక్ష మాత్రమే ఖచ్చితమైనది.",
  },
};

/**
 * Explanations when no findings exceed the operating threshold.
 */
export const CXR_BELOW_THRESHOLD_EXPLANATIONS = {
  en: {
    title: "No Findings Above Operating Threshold",
    summary:
      "The experimental computer model did not identify any of the 18 evaluated thoracic patterns with a score exceeding its prototype threshold in this radiograph.",
    caution:
      "Important Clinical Caution: This does NOT prove your lungs are completely healthy or rule out chest conditions. Subtle infections, early nodules, or non-evaluated conditions may still be present. A clinical examination by a qualified doctor is always required.",
  },
  ta: {
    title: "எந்தவொரு பாதிப்பும் வரம்பை தாண்டவில்லை",
    summary:
      "இந்த எக்ஸ்-ரே படத்தில் ஆய்வு செய்யப்பட்ட 18 மார்பு நோய்க்கூறுகளில் எதுவும் சோதனை வரம்பை விட அதிகமாக மாதிரியால் கண்டறியப்படவில்லை.",
    caution:
      "முக்கிய எச்சரிக்கை: இது உங்கள் நுரையீரல் முழுமையாக ஆரோக்கியமாக உள்ளது என்பதற்கான சான்றோ அல்லது நோய் இல்லை என்பதற்கான உத்தரவாதமோ அல்ல. மருத்துவரின் நேரடி பரிசோதனை எப்போதும் அவசியமாகும்.",
  },
  hi: {
    title: "कोई भी लक्षण थ्रेशोल्ड सीमा से ऊपर नहीं मिला",
    summary:
      "इस एक्स-रे में जांची गई 18 वक्षीय स्थितियों में से किसी का भी स्कोर प्रयोगात्मक थ्रेशोल्ड से अधिक नहीं पाया गया।",
    caution:
      "महत्वपूर्ण नैदानिक चेतावनी: इसका अर्थ यह नहीं है कि फेफड़े पूरी तरह स्वस्थ हैं या बीमारी की कोई संभावना नहीं है। योग्य चिकित्सक द्वारा प्रत्यक्ष परीक्षण अनिवार्य है।",
  },
  te: {
    title: "ఎటువంటి లక్షణాలు పరిమితిని మించలేదు",
    summary:
      "ఈ ఎక్స్-రేలో పరిశీలించిన 18 థొరాసిక్ వ్యాధి నమూనాలలో ఏవీ ప్రయోగాత్మక పరిమితిని మించి నమోదు కాలేదు.",
    caution:
      "ముఖ్యమైన వైద్య హెచ్చరిక: ఇది ఊపిరితిత్తులు పూర్తిగా ఆరోగ్యంగా ఉన్నాయని లేదా వ్యాధి లేదని నిరూపించదు. వైద్యుని ప్రత్యక్ష పరీక్ష ఎల్లప్పుడూ అవసరం.",
  },
};

/**
 * Emergency Red-Flag Warning Signs in all 4 languages.
 */
export const CXR_EMERGENCY_WARNINGS = {
  en: {
    title: "When to Seek Immediate Emergency Medical Care",
    intro:
      "An AI chest X-ray screening tool cannot evaluate urgent or life-threatening symptoms. Call emergency medical services or visit the nearest emergency room immediately if you experience:",
    symptoms: [
      "Sudden, severe, or worsening shortness of breath or difficulty breathing",
      "Sharp, crushing chest pain that spreads to your arm, neck, jaw, or back",
      "Coughing up significant amounts of fresh red blood (hemoptysis)",
      "Bluish color in your lips, tongue, face, or fingertips (cyanosis)",
      "Sudden confusion, dizziness, fainting, or inability to stay awake",
    ],
    instruction:
      "Do NOT wait for online results or email responses if you have any of these emergency warning signs.",
  },
  ta: {
    title: "உடனடி அவசர மருத்துவ உதவி எப்போது தேவை?",
    intro:
      "ஒரு செயற்கை நுண்ணறிவு மாதிரி உயிருக்கு ஆபத்தான அவசர நிலைகளை கையாள முடியாது. பின்வரும் அறிகுறிகள் ஏதேனும் இருந்தால் உடனே அவசர சிகிச்சை பிரிவை அணுகவும்:",
    symptoms: [
      "திடீர் கடுமையான மூச்சுத்திணறல் அல்லது சுவாசிப்பதில் தீவிர சிரமம்",
      "தோள்பட்டை, கழுத்து அல்லது தாடைக்கு பரவும் கடுமையான நெஞ்சு வலி",
      "இருமும் போது புதிய இரத்தம் வெளியேறுதல்",
      "உதடுகள், முகம் அல்லது விரல் நகங்கள் நீல நிறமாக மாறுதல்",
      "திடீர் தலைசுற்றல், மயக்கம் அல்லது சுயநினைவு இழத்தல்",
    ],
    instruction:
      "இத்தகைய அவசர எச்சரிக்கை அறிகுறிகள் இருந்தால் ஆன்லைன் முடிவுகளுக்காக காத்திருக்காமல் உடனடியாக அவசர மருத்துவ உதவியை நாடவும்.",
  },
  hi: {
    title: "तत्काल आपातकालीन चिकित्सा देखभाल कब लें?",
    intro:
      "एआई उपकरण जीवन-घातक आपात स्थितियों का इलाज नहीं कर सकता। यदि आप निम्न में से कोई भी लक्षण महसूस करें तो तुरंत निकटतम आपातकालीन अस्पताल जाएं:",
    symptoms: [
      "अचानक गंभीर सांस फूलना या सांस लेने में अत्यधिक कठिनाई",
      "सीने में तेज दबाव या दर्द जो बांह, गर्दन या जबड़े तक फैले",
      "खांसी में ताजा लाल खून आना",
      "होंठों, चेहरे या नाखूनों का नीला पड़ना",
      "अचानक चक्कर आना, बेहोशी या भ्रम की स्थिति",
    ],
    instruction:
      "इनमें से कोई भी लक्षण होने पर ऑनलाइन नतीजों का इंतजार न करें, तुरंत आपातकालीन सहायता लें।",
  },
  te: {
    title: "తక్షణ అత్యవసర వైద్య సంరక్షణ ఎప్పుడు అవసరం?",
    intro:
      "AI స్క్రీనింగ్ సాధనం అత్యవసర పరిస్థితులను అంచనా వేయలేదు. కింది లక్షణాలు ఏవైనా ఉంటే వెంటనే అత్యవసర విభాగాన్ని ఆశ్రయించండి:",
    symptoms: [
      "అకస్మాత్తుగా తీవ్రమైన ఆయాసం లేదా శ్వాస తీసుకోవడంలో ఇబ్బంది",
      "చేయి, మెడ లేదా దవడకు వ్యాపించే తీవ్రమైన ఛాతీ నొప్పి",
      "దగ్గినప్పుడు రక్తం పడటం",
      "పెదవులు లేదా వేళ్లు నీలిరంగులోకి మారడం",
      "అకస్మాత్తుగా తలతిరగడం, స్పృహ కోల్పోవడం",
    ],
    instruction:
      "ఈ అత్యవసర లక్షణాలు ఉంటే ఆలస్యం చేయకుండా వెంటనే ఆసుపత్రికి వెళ్లండి.",
  },
};

/**
 * Localized UI Strings for the Chest X-ray Patient Explanation component.
 */
export const CXR_UI_STRINGS = {
  en: {
    sectionHeading: "Understand Your Chest X-Ray Result",
    sectionSubheading:
      "Plain-language explanation of findings, visual attention heatmaps, and evidence-based guidance.",
    languageToggleLabel: "Select Language",
    readAloud: "Listen (Read Aloud)",
    pauseAudio: "Pause Audio",
    resumeAudio: "Resume Audio",
    stopAudio: "Stop Audio",
    audioPlaying: "Reading aloud in English...",
    audioPaused: "Audio paused.",
    audioFinished: "Audio finished.",
    audioUnavailable:
      "Text-to-speech is not supported in this browser. Please read the explanation above.",
    voiceUnavailable:
      "English voice synthesizer is not available on this device. Please read the text above.",
    tamilVoiceUnavailable:
      "Tamil voice is not installed on this device. Please install the Tamil voice pack or read the text above.",
    confidenceTitle: "Model Score & Calibration",
    disclaimerBannerTitle: "Educational & Research Notice",
    disclaimerBannerText:
      "This patient-friendly guidance is strictly for educational understanding and is NOT a medical diagnosis. A licensed radiologist or pulmonologist must evaluate your chest radiograph.",
    noPrediction: "No Chest X-ray prediction data is available to explain.",
  },
  ta: {
    sectionHeading: "உங்கள் மார்பு எக்ஸ்-ரே முடிவை புரிந்து கொள்ளுங்கள்",
    sectionSubheading:
      "கண்டுபிடிப்புகள், கவன வரைபடங்கள் மற்றும் அடுத்த கட்ட நடவடிக்கைகள் பற்றிய எளிய விளக்கம்.",
    languageToggleLabel: "மொழியைத் தேர்ந்தெடுக்கவும்",
    readAloud: "கேளுங்கள் (ஒலி வடிவம்)",
    pauseAudio: "நிறுத்துக",
    resumeAudio: "தொடர்க",
    stopAudio: "முடிக்க",
    audioPlaying: "தமிழில் வாசிக்கப்படுகிறது...",
    audioPaused: "ஒலி தற்காலிகமாக நிறுத்தப்பட்டது.",
    audioFinished: "ஒலி வாசிப்பு முடிந்தது.",
    audioUnavailable:
      "இந்த உலாவியில் ஒலி வாசிப்பு வசதி இல்லை. மேற்கண்ட உரையை நேரடியாக வாசிக்கவும்.",
    voiceUnavailable:
      "இந்த மொழிக்கான குரல் வசதி இந்த சாதனத்தில் இல்லை. மேற்கண்ட உரையை நேரடியாக வாசிக்கவும்.",
    tamilVoiceUnavailable:
      "இந்த சாதனத்தில் தமிழ் குரல் வசதி கிடைக்கவில்லை. அமைப்புகளில் தமிழ் குரலை இயக்கவும் அல்லது உரையை வாசிக்கவும்.",
    confidenceTitle: "மாதிரி மதிப்பெண் & கணக்கீடு",
    disclaimerBannerTitle: "கல்வி மற்றும் ஆராய்ச்சி அறிவிப்பு",
    disclaimerBannerText:
      "இந்த விளக்கம் கல்வி புரிதலுக்காக மட்டுமே; இது மருத்துவ நோயறிதல் அல்ல. உரிமம் பெற்ற மருத்துவ நிபுணரின் நேரடி பரிசோதனைக்கு இது ஈடாகாது.",
    noPrediction: "விளக்குவதற்கு எந்த எக்ஸ்-ரே கணிப்பு தகவலும் கிடைக்கவில்லை.",
  },
  hi: {
    sectionHeading: "अपने छाती के एक्स-रे परिणाम को समझें",
    sectionSubheading:
      "वक्षीय निष्कर्षों, एआई ध्यान और साक्ष्य-आधारित मार्गदर्शन की सरल भाषा में व्याख्या।",
    languageToggleLabel: "भाषा चुनें",
    readAloud: "सुनें (बोलकर पढ़ें)",
    pauseAudio: "रोकें",
    resumeAudio: "जारी रखें",
    stopAudio: "समाप्त करें",
    audioPlaying: "हिन्दी में प्रतिक्रिया सुनाई जा रही है...",
    audioPaused: "ऑडियो रुका हुआ है।",
    audioFinished: "ऑडियो पूरा हुआ।",
    audioUnavailable:
      "इस ब्राउज़र में टेक्स्ट-टू-स्पीच समर्थित नहीं है। कृपया ऊपर दिया गया पाठ पढ़ें।",
    voiceUnavailable:
      "इस भाषा के लिए आपके उपकरण पर आवाज़ स्थापित नहीं है। कृपया ऊपर दिया गया पाठ पढ़ें।",
    tamilVoiceUnavailable:
      "इस भाषा की आवाज़ आपके उपकरण पर नहीं मिली। कृपया ऊपर दिया गया पाठ पढ़ें।",
    confidenceTitle: "मॉडल स्कोर और निश्चितता",
    disclaimerBannerTitle: "शैक्षिक एवं अनुसंधान सूचना",
    disclaimerBannerText:
      "यह व्याख्या केवल शैक्षिक समझ के लिए है और व्यक्तिगत चिकित्सा सलाह नहीं है। यह किसी योग्य चिकित्सक द्वारा नैदानिक परीक्षण का विकल्प नहीं है।",
    noPrediction: "समझाने के लिए कोई एक्स-रे परिणाम उपलब्ध नहीं है।",
  },
  te: {
    sectionHeading: "మీ ఛాతీ ఎక్స్-రే ఫలితాన్ని అర్థం చేసుకోండి",
    sectionSubheading:
      "థొరాసిక్ ఫలితాలు, AI శ్రద్ధ మరియు మార్గదర్శకాల గురించి సరళమైన వివరణ.",
    languageToggleLabel: "భాషను ఎంచుకోండి",
    readAloud: "వినండి (వాయిస్ ద్వారా)",
    pauseAudio: "ఆపు",
    resumeAudio: "కొనసాగించు",
    stopAudio: "ముగించు",
    audioPlaying: "తెలుగులో చదవబడుతోంది...",
    audioPaused: "ఆడియో పాజ్ చేయబడింది.",
    audioFinished: "ఆడియో పూర్తయింది.",
    audioUnavailable:
      "ఈ బ్రౌజర్‌లో టెక్స్ట్-టు-స్పీచ్ సదుపాయం లేదు. దయచేసి పై వచనాన్ని చదవండి.",
    voiceUnavailable:
      "ఈ భాష కోసం ఈ పరికరంలో వాయిస్ ఇన్‌స్టాల్ చేయబడలేదు. దయచేసి పై వచనాన్ని చదవండి.",
    tamilVoiceUnavailable:
      "ఈ భాష వాయిస్ అందుబాటులో లేదు. దయచేసి పై వచనాన్ని చదవండి.",
    confidenceTitle: "మోడల్ స్కోరు & ఖచ్చితత్వం",
    disclaimerBannerTitle: "విద్యా & పరిశోధన నోటీసు",
    disclaimerBannerText:
      "ఈ వివరణ కేవలం అవగాహన కోసం మాత్రమే మరియు ఇది వైద్య సలహా కాదు. ఇది నిపుణుడైన వైద్యుడి ప్రత్యక్ష పరీక్షకు ప్రత్యామ్నాయం కాదు.",
    noPrediction: "వివరించడానికి ఎలాంటి ఎక్స్-రే ఫలితం అందుబాటులో లేదు.",
  },
};

/**
 * Returns a patient-friendly finding explanation object for a given pathology name and language.
 *
 * @param {string} findingName - Model pathology name (e.g. 'Atelectasis', 'Cardiomegaly')
 * @param {string} [lang='en'] - Language code ('en', 'ta', 'hi', 'te')
 * @returns {Object} Finding explanation data
 */
export function getChestXrayFindingExplanation(findingName, lang = "en") {
  const normKey = findingName ? findingName.trim() : "Atelectasis";
  const item =
    CXR_PATHOLOGY_EXPLANATIONS[normKey] ||
    CXR_PATHOLOGY_EXPLANATIONS[normKey.replace(/_/g, " ")] ||
    CXR_PATHOLOGY_EXPLANATIONS[normKey.replace(/ /g, "_")] ||
    CXR_PATHOLOGY_EXPLANATIONS.Atelectasis;

  const validLang = ["en", "ta", "hi", "te"].includes(lang) ? lang : "en";
  return {
    clinicalLabel: item.clinicalLabel,
    ...(item[validLang] || item.en),
  };
}
