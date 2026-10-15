"""Reviewed official-site guide. No old SaaS articles are used to answer."""
import json
import re
from pathlib import Path

CHECKED = '2026-10-13'
GUIDES = json.loads((Path(__file__).parent / 'data' / 'kapture_guide.json').read_text(encoding='utf-8'))
GREETING = 'Hello. I am Voxera, an independent AI website guide for Kapture CX, not an official Kapture representative. Ask what the company does, how to apply for jobs, request a demo, or contact them. I explain public website information; I cannot submit forms or access accounts.'
GREETING_HI = 'नमस्ते। मैं Kapture CX की वेबसाइट समझाने वाला स्वतंत्र AI सहायक Voxera हूँ। मैं Kapture का आधिकारिक प्रतिनिधि नहीं हूँ। कंपनी, नौकरी के आवेदन, डेमो या संपर्क के बारे में पूछें। मैं वेबसाइट की सार्वजनिक जानकारी बताता हूँ; फ़ॉर्म जमा नहीं कर सकता और खातों तक पहुँच नहीं है।'
FALLBACK = 'I could not verify a specific answer in the reviewed Kapture website guide. Please check the relevant official page or contact Kapture directly. I cannot invent job openings, salaries, prices, account details, or promises.'
FALLBACK_HI = 'Kapture की जाँची गई वेबसाइट जानकारी में मुझे इसका पक्का उत्तर नहीं मिला। कृपया संबंधित आधिकारिक पेज देखें या Kapture से सीधे संपर्क करें। मैं नौकरी, वेतन, कीमत, खाते या किसी वादे के बारे में अनुमान नहीं लगाऊँगा।'
HI = {
'About Kapture CX':'Kapture CX अपने आपको AI-संचालित ग्राहक अनुभव प्लेटफ़ॉर्म बताता है। इसकी वेबसाइट AgentOS को ऐसा प्लेटफ़ॉर्म बताती है जो एंटरप्राइज़ वर्कफ़्लो में AI एजेंट और मानवीय बुद्धिमत्ता को साथ लाता है। कंपनी के बारे में जानने के लिए kapture डॉट c x खोलें, Company चुनें, फिर About Us चुनें। Voxera स्वतंत्र वेबसाइट गाइड है, Kapture का आधिकारिक प्रतिनिधि नहीं।',
'Apply for jobs at Kapture CX':'नौकरी के लिए Kapture की आधिकारिक वेबसाइट खोलें और Company, फिर Careers चुनें। उपलब्ध भूमिकाएँ देखें और ज़रूरत हो तो Load More चुनें। उपयुक्त भूमिका खोलें और उसके Keka आवेदन लिंक का पालन करें। आवेदन की शर्तें और पद अभी खुला है या नहीं, यह भूमिका के पेज पर जाँचें। नौकरी के लिए demo फ़ॉर्म न भरें। मैं आवेदन जमा नहीं कर सकता और न ही पद उपलब्ध होने की पुष्टि कर सकता हूँ।',
'Kapture hiring process':'Kapture का Careers पेज आवेदन और रिज़्यूमे की समीक्षा, Talent Acquisition की स्क्रीनिंग कॉल, तकनीकी इंटरव्यू, नेतृत्व चर्चा, चयनित उम्मीदवारों के दस्तावेज़ और आंतरिक मंज़ूरी के बाद प्रस्ताव का वर्णन करता है। हर पद की प्रक्रिया अलग हो सकती है। समय-सीमा, पात्रता, वेतन और वर्चुअल इंटरव्यू सीधे Kapture से सत्यापित करें।',
'Contact Kapture CX':'Kapture से संपर्क करने के लिए आधिकारिक वेबसाइट पर Company, फिर Contact Us खोलें। सामान्य पूछताछ के लिए वेबसाइट enquiries at kapture डॉट c x दिखाती है। नौकरी के लिए Careers पेज देखें; उत्पाद सहायता के लिए Support पेज खोलें। जाँचे गए पेजों पर फ़ोन नंबरों का प्रारूप अलग है, इसलिए कॉल करने से पहले Contact Us पर नंबर जाँच लें। यह डेमो Kapture कर्मचारी से नहीं जोड़ता और न ही कॉलबैक का वादा करता है।',
'Request a Kapture demo':'Kapture वेबसाइट पर Personalized Demo चुनें या kapture डॉट c x slash demo खोलें। फ़ॉर्म में पूरा नाम, कार्य ईमेल, देश-कोड सहित फ़ोन और कंपनी पूछी जाती है। सहमति देने से पहले गोपनीयता सूचना पढ़ें; सहमत हों तो Get Started दबाएँ। डेमो पेज AgentOS प्रदर्शन, उपयोग-मामले पर चर्चा और कोट सलाह बताता है। मैं आपकी जानकारी जमा नहीं करूँगा और न ही निःशुल्क ट्रायल या मीटिंग का वादा करूँगा।',
'Kapture products and AgentOS':'Kapture के Products में AgentOS और इसकी चार परतें दिखाई गई हैं: VITOS AI एजेंट बनाने, जाँचने और तैनात करने के लिए; COMMAND वर्कफ़्लो में मनुष्य कहाँ शामिल हों यह तय करने के लिए; CALIBRATE इंटरैक्शन की समीक्षा के लिए; और PULSE परिचालन डेटा पर प्रश्न और विश्लेषण के लिए। विवरण संबंधित आधिकारिक उत्पाद पेज पर देखें।',
'Kapture pricing and quotes':'Kapture के Pricing पेज के अनुसार मॉड्यूलर कीमत उत्पाद, उपयोगकर्ताओं की संख्या, इंटरैक्शन और AI सुविधाओं पर निर्भर करती है। एजेंट-आधारित, इंटरैक्शन-आधारित या मिश्रित विकल्प हो सकते हैं। वास्तविक कीमत के लिए कस्टम कोट या डेमो माँगें। मेरे पास आपकी कंपनी की सत्यापित निश्चित कीमत नहीं है; मैं रिफ़ंड, रद्दीकरण या अनुबंध बदलाव मंज़ूर नहीं कर सकता।',
'Existing customer support and login':'मौजूदा ग्राहक सहायता के लिए Kapture का आधिकारिक Support पेज खोलें। वहाँ नाम, ईमेल, फ़ोन, कंपनी, टिप्पणी और गोपनीयता सहमति वाला फ़ॉर्म है। लॉगिन के लिए अपने संगठन का अधिकृत लिंक इस्तेमाल करें या प्रशासक से पूछें; मैंने कोई सार्वभौमिक लॉगिन URL सत्यापित नहीं किया है। पासवर्ड, OTP, API कुंजी या ग्राहक रिकॉर्ड इस डेमो से साझा न करें।',
'Kapture office location':'Kapture के Contact पेज पर बेंगलुरु मुख्य कार्यालय B-9, 11वीं मंज़िल, Brigade Summit, ITPL Main Road, Brigade Metropolis, Garudachar Palya, Mahadevapura, Bengaluru, Karnataka 560048 दिया गया है। वहाँ USA, मुंबई, गुरुग्राम और UAE कार्यालय भी सूचीबद्ध हैं। जाने से पहले पता और आगंतुक निर्देश कंपनी से जाँचें।',
'Website navigation':'www डॉट kapture डॉट c x से शुरू करें। Products में प्लेटफ़ॉर्म, Solutions में उद्योग, Pricing में व्यावसायिक जानकारी और Resources में ब्लॉग, केस स्टडी, इंटीग्रेशन व API दस्तावेज़ मिलते हैं। Company में About Us, Careers, Partners, Contact Us और Trust Center हैं। डेमो के लिए Personalized Demo चुनें। नौकरी के लिए Careers पर जाएँ, डेमो फ़ॉर्म पर नहीं। मोबाइल पर मेनू बदल सकता है।',
'Kapture integrations and developer documentation':'Kapture वेबसाइट पर Resources, फिर Integrations खोलकर CRM, कॉलिंग, WhatsApp, सोशल मीडिया, ई-कॉमर्स, लॉजिस्टिक्स, भुगतान और ERP इंटीग्रेशन देखें। डेवलपर दस्तावेज़ dev डॉट kapture डॉट c x slash kapture dash api पर हैं। उपलब्धता और सेटअप की पुष्टि Kapture से करें; API सीक्रेट साझा न करें।',
'Kapture partnerships':'Kapture वेबसाइट पर Company, फिर Partners चुनें। पेज Business Transformation, Consulting and Advisory, और Technology-First पार्टनरशिप मॉडल बताता है। पात्रता जानने के लिए आधिकारिक पेज और संपर्क मार्ग का उपयोग करें। मैं साझेदारी, कमीशन या व्यावसायिक शर्तें मंज़ूर नहीं कर सकता।',
'Kapture trust, security, and privacy':'Kapture की प्रकाशित सुरक्षा, अनुपालन और जिम्मेदार AI जानकारी के लिए Company, फिर Trust Center खोलें। ये कंपनी के अपने दावे हैं, Voxera का स्वतंत्र सुरक्षा ऑडिट नहीं। अपनी आवश्यकताओं के प्रमाण Kapture से माँगें और व्यक्तिगत जानकारी देने से पहले Privacy Policy पढ़ें। यह न मानें कि हर प्रमाणपत्र हर उत्पाद या तैनाती पर लागू है।'
}


def answer(message, language='en-IN'):
    text = message.lower().strip()
    hindi = language == 'hi-IN'
    fallback = FALLBACK_HI if hindi else FALLBACK
    if len(text) > 2000:
        return fallback, 0.0, 'safe_fallback', None
    if re.search(r'\b(ignore.*instructions|system prompt|salary|salaries|guarantee|guaranteed|otp|my application status|my ticket status|currently hiring|current vacancies|latest vacancies|open jobs today|refund approved)\b', text):
        return fallback, 0.0, 'safe_fallback', {'title':'Check official Kapture information', 'url':'https://www.kapture.cx/contact/', 'checked_at':CHECKED}
    if text in {'hi','hello','hey','good morning'}:
        return (GREETING_HI if hindi else GREETING), 1.0, 'knowledge_base', {'title':'Kapture official website','url':'https://www.kapture.cx/','checked_at':CHECKED}
    order = [2,1,4,6,8,10,11,12,7,5,3,9,0]
    matches = [GUIDES[i] for i in order if re.search(GUIDES[i]['pattern'],text)]
    if not matches:
        return fallback, 0.0, 'safe_fallback', {'title':'Kapture official website','url':'https://www.kapture.cx/','checked_at':CHECKED}
    guide = matches[0]
    content = HI.get(guide['title'], guide['content']) if hindi else guide['content']
    return content, 0.9, 'knowledge_base', {'title':guide['title'], 'url':guide['url'], 'checked_at':CHECKED,'version':1,'steps':[], 'scope':'official-site guide, not live account data'}
