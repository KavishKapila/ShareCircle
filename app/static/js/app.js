(() => {
  const root = document.documentElement;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('/static/sw.js').catch(() => {}));

  const translations = {
    en: {
      'a11y.skip':'Skip to content', 'nav.home':'Home','nav.browse':'Browse','nav.nearby':'Nearby','nav.dashboard':'Dashboard','nav.impact':'Impact','nav.leaderboard':'Leaderboard','nav.judge':'Judge Mode','nav.hackathon':'Hackathon Utilities','nav.post_need_offer':'Post Need / Offer','nav.notifications':'Notifications','nav.theme':'Toggle dark mode','nav.logout':'Log out','nav.login':'Log in','nav.join':'Join','nav.post':'Post',
      'footer.tagline':'Local help, one match at a time.',
      'hackathon.eyebrow':'HACKATHON UTILITIES','hackathon.title':'Quick judge accounts','hackathon.copy':'Create a quick test account in one click. It behaves like a normal ShareCircle account, but judges can switch between quick accounts without a password.','hackathon.create':'Create & switch to a quick account','hackathon.switch':'Switch quick account','hackathon.current':'Current','hackathon.note':'Quick accounts are clearly marked for hackathon testing and are stored in this app database so judges can use the normal product flow.','sheet.eyebrow':'CREATE','sheet.title':'What would you like to post?','sheet.need':'Post a Need','sheet.need_hint':'Ask your neighborhood for help.','sheet.offer':'Post an Offer','sheet.offer_hint':'Share a skill, item, ride, or time.','modal.close':'Close',
      'stats.members':'Members','stats.needs':'Needs','stats.offers':'Offers','stats.completed':'Completed','stats.points':'Impact Points',
      'home.eyebrow':'NEIGHBORHOOD POWERED','home.title':'Help moves when people overlap.','home.subtitle':'Post a need. Share what you can. Meet a neighbor and make the help real.','home.cta':'Join the circle','home.secondary':'Explore needs','home.demo':'Run the demo','home.trust.free':'Free to use','home.trust.otp':'Verified by OTP','home.trust.private':'Private until matched','home.ripple_hint':'Move. Tap. Watch the circle respond.','home.stats.members_hint':'neighbors in the circle','home.stats.needs_hint':'requests shared with the circle','home.stats.offers_hint':'skills ready to share','home.stats.completed_hint':'real-world helps delivered','home.completed.eyebrow':'RECENTLY COMPLETED','home.completed.title':'Real help, recently delivered.','home.completed.empty':'Your first completed match will appear here.','home.open.eyebrow':'OPEN IN THE CIRCLE','home.open.title':'Needs neighbors can see now.','home.open.link':'Browse all','home.open.empty':'No open needs yet. Be the first to post one.','home.how.eyebrow':'HOW IT WORKS','home.how.title':'Four moves. One visible act of help.','home.how.one':'Post a need','home.how.one_copy':'Share what would make your week easier, from tutoring to transport.','home.how.two':'Find your overlap','home.how.two_copy':'Nearby matches appear around you, with reasons you can understand.','home.how.three':'Move together','home.how.three_copy':'Accepted, arrived, paid. The circles draw closer as the real-world help happens.','home.how.four':'Leave a mark','home.how.four_copy':'OTP verifies the handoff. Points and a shareable receipt make the impact visible.','home.ready.eyebrow':'READY TO HELP?','home.ready.title':'Start with one small overlap.','home.ready.cta':'Create your profile',
      'location.title':'Add a location','location.subtitle':'Use your device coordinates or type an area. ShareCircle never silently requests location.','location.use':'Use my location','location.clear':'Clear','location.area':'Area','location.none':'No location added. You can still publish this post.','location.save':'Save location',
      'form.need.eyebrow':'ASK YOUR CIRCLE','form.need.title':'Post a Need','form.need.subtitle':'Be specific enough for a good match, but keep it human.','form.need.submit':'Publish need','form.offer.eyebrow':'SHARE WHAT YOU CAN','form.offer.title':'Post an Offer','form.offer.subtitle':'Your hour, ride, skill, item, or meal can unlock someone else’s day.','form.offer.submit':'Publish offer','form.title':'Title','form.description':'Description','form.category':'Category','form.urgency':'Urgency','form.availability':'Availability','form.price':'Price','form.price_hint':'Set the amount the helper should expect for this need. This is shown before someone accepts.','detail.price':'PRICE','detail.price_copy':'Helper payment expected for this need.',
      'urgency.low':'Low','urgency.medium':'Medium','urgency.high':'High',
      'auth.login.eyebrow':'WELCOME BACK','auth.login.title':'Log in to your circle.','auth.login.subtitle':'Use your username or email.','auth.identifier':'Username or email','auth.password':'Password','auth.remember':'Keep me signed in','auth.forgot':'Forgot password?','auth.login.submit':'Log in','auth.new_here':'New here?','auth.create':'Create an account','auth.browse':'Continue browsing','auth.signup.eyebrow':'JOIN THE CIRCLE','auth.signup.title':'Create your profile.','auth.signup.subtitle':'A few basics, then you can start asking and offering.','auth.full_name':'Full name','auth.username':'Username','auth.username_hint':'3+ characters. Availability checks as you type.','auth.email':'Email','auth.location':'Location','auth.location_hint':'Choose a neighborhood or city, or type a more specific area.','auth.continue':'Continue','auth.password_hint':'A longer password is safer; use 8+ characters with a mix of letters, numbers, or symbols.','auth.back':'Back','auth.signup.submit':'Create account','auth.already':'Already joined?','auth.login_link':'Log in','auth.forgot_title':'Forgot your password?','auth.forgot_copy':'Enter your account email. ShareCircle will show the next available recovery step.','auth.forgot_submit':'Request reset','auth.back_login':'Back to log in',
      'nearby.eyebrow':'YOUR LOCAL CIRCLE','nearby.title':'Needs inside your radius.','nearby.subtitle':'Tap a signal to see the need, or use the accessible list below.','nearby.add_offer':'Add another offer','nearby.change':'Change','nearby.manual_hint':'Manual mode never needs browser permission.','nearby.ready':'Ready to find nearby needs','nearby.you_offer':'You offer:','nearby.offer_hint':'Post an offer to unlock nearby matching needs.','nearby.list_view':'List','nearby.circle_view':'Circle field',
      'match.back':'Dashboard','live.label':'Live','live.updated':'updated just now','match.chat_eyebrow':'MATCH CHAT','match.chat_title':'Keep the handoff clear.','live.messages':'Messages update live','match.chat_loading':'Loading messages…','match.send':'Send','match.job':'THE JOB','match.need_owner':'Need owner','match.helper':'Helper','match.directions':'Open directions','match.safety':'Safety first','match.safety_copy':'Meet in a public place, share your trip, and keep payment details private.','match.share_trip':'Share my trip','match.report':'Report / Block',
      'dashboard.eyebrow':'YOUR CIRCLE','dashboard.subtitle':'Keep your asks moving and your generosity visible.','dashboard.to_badge':'to next badge','dashboard.post_need':'Post Need','dashboard.post_offer':'Post Offer','dashboard.nearby':'Nearby needs','dashboard.profile':'View profile','dashboard.open_match':'Open match','dashboard.needs':'My Needs','dashboard.offers':'My Offers','dashboard.get_started':'GET STARTED','dashboard.build_title':'Build your circle in three moves.','dashboard.step_need':'Post your first need','dashboard.step_need_hint':'Ask for local help.','dashboard.step_offer':'Add an offer','dashboard.step_offer_hint':'Share something useful.','dashboard.step_nearby':'Open Nearby','dashboard.step_nearby_hint':'Find people close to you.',
      'browse.eyebrow':'THE CIRCLE BOARD','browse.title':'See what your neighborhood can share.','browse.subtitle':'Search public needs and offers. Category and urgency stay one tap away.','browse.needs':'Needs','browse.offers':'Offers','browse.category':'CATEGORY','browse.all':'All','browse.urgency':'URGENCY','browse.any':'Any','browse.load_more':'Load more',
      'impact.eyebrow':'COMMUNITY IMPACT','impact.title':'One completed match becomes one more mark on the neighborhood.','impact.subtitle':'Live platform totals, rendered as a living rangoli of completed help.','impact.completed.eyebrow':'WHERE HELP LANDS','impact.completed.title':'Top categories by completed matches','impact.completed.empty':'Complete your first match to light up the chart.','impact.rangoli.eyebrow':'THE COMMUNITY RANGOLI','impact.rangoli.title':'Every help leaves a petal.','impact.supply.eyebrow':'SUPPLY & DEMAND','impact.supply.title':'Where the circle needs more hands.','impact.supply.subtitle':'Open needs compared with available offers, by category.','impact.supply.empty':'Post a need or offer to populate this live gauge.',
      'receipt.back':'Back to match','receipt.print':'Print / Save as PDF','receipt.share_button':'Share receipt','receipt.eyebrow':'SHARECIRCLE · COMMUNITY IMPACT','receipt.title':'Impact Receipt','receipt.match':'Match','receipt.completed':'Completed','receipt.need_owner':'Need owner','receipt.helper':'Helper','receipt.need':'Need','receipt.category':'Category','receipt.amount':'Amount recorded','receipt.impact_points':'Impact Points','receipt.thanks':'Thank you for turning a neighborhood need into a completed match.','receipt.share':'Keep this receipt as a simple, tangible record of community impact.',
      'profile.eyebrow':'COMMUNITY MEMBER','profile.needs':'Needs','profile.offers':'Offers','profile.activity':'Activity','leaderboard.eyebrow':'VISIBLE GENEROSITY','leaderboard.title':'Impact leaders.','leaderboard.subtitle':'Impact Points are earned through completed ShareCircle help.','leaderboard.member':'Member','leaderboard.location':'Location','leaderboard.points':'Points','leaderboard.rating':'Rating','leaderboard.empty':'No members yet',
      'detail.need_published':'Need published.','detail.need_published_copy':'Your request is live in the circle.','detail.can_help':'Can you help nearby?','detail.can_help_copy':'Your available offer can be matched to this request.','detail.accept':'Accept this need','detail.want_help':'Want to help?','detail.want_help_copy':'Sign in to accept this need.','detail.matches':'SMART MATCHES','detail.matches_title':'People who can help','detail.matches_copy':'The match score uses category, keywords, urgency, and reputation.','detail.offer_published':'Offer published.','detail.offer_published_copy':'Your skill is now available to the circle.','detail.explore':'Explore needs','detail.availability':'AVAILABILITY'
    },
    hi: {
      'nav.home':'होम','nav.browse':'ब्राउज़','nav.nearby':'पास में','nav.dashboard':'डैशबोर्ड','nav.impact':'प्रभाव','nav.leaderboard':'लीडरबोर्ड','nav.judge':'जज मोड','nav.hackathon':'हैकाथॉन यूटिलिटीज़','nav.post_need_offer':'पोस्ट ज़रूरत / ऑफ़र','nav.notifications':'सूचनाएँ','nav.theme':'डार्क मोड बदलें','nav.logout':'लॉग आउट','nav.login':'लॉग इन','nav.join':'जुड़ें','nav.post':'पोस्ट',
      'hackathon.eyebrow':'हैकाथॉन यूटिलिटीज़','hackathon.title':'त्वरित जज अकाउंट','hackathon.copy':'एक क्लिक में टेस्ट अकाउंट बनाएँ। यह सामान्य ShareCircle अकाउंट की तरह काम करता है, लेकिन जज बिना पासवर्ड के क्विक अकाउंट बदल सकते हैं।','hackathon.create':'बनाएँ और क्विक अकाउंट पर जाएँ','hackathon.switch':'क्विक अकाउंट बदलें','hackathon.current':'वर्तमान','hackathon.note':'क्विक अकाउंट हैकाथॉन टेस्टिंग के लिए स्पष्ट रूप से चिह्नित हैं और सामान्य प्रोडक्ट फ्लो के लिए इसी ऐप डेटाबेस में सेव होते हैं।','footer.tagline':'स्थानीय मदद, एक मैच एक समय में।','sheet.eyebrow':'बनाएँ','sheet.title':'आप क्या पोस्ट करना चाहते हैं?','sheet.need':'ज़रूरत पोस्ट करें','sheet.need_hint':'अपने पड़ोस से मदद माँगें।','sheet.offer':'मदद का ऑफ़र पोस्ट करें','sheet.offer_hint':'समय, कौशल, सामान या मदद साझा करें।','modal.close':'बंद करें','stats.members':'सदस्य','stats.needs':'ज़रूरतें','stats.offers':'ऑफ़र','stats.completed':'पूरे हुए','stats.points':'इम्पैक्ट पॉइंट्स',
      'home.eyebrow':'पड़ोस से चलने वाली मदद','home.title':'जहाँ लोग मिलते हैं, मदद चल पड़ती है।','home.subtitle':'ज़रूरत पोस्ट करें। जो आप कर सकते हैं साझा करें। एक पड़ोसी से मिलें और मदद को सच बनाएं।','home.cta':'सर्कल में जुड़ें','home.secondary':'ज़रूरतें देखें','home.demo':'डेमो चलाएँ','home.trust.free':'मुफ़्त उपयोग','home.trust.otp':'OTP से सत्यापन','home.trust.private':'मैच तक निजी','home.ripple_hint':'हिलें। टैप करें। सर्कल को जवाब देते देखें।','home.stats.members_hint':'सर्कल के पड़ोसी','home.stats.needs_hint':'साझा की गई ज़रूरतें','home.stats.offers_hint':'साझा करने को तैयार कौशल','home.stats.completed_hint':'पूरी हुई मदद','home.completed.eyebrow':'हाल में पूरे हुए','home.completed.title':'अभी-अभी पहुँची असली मदद।','home.completed.empty':'आपका पहला पूरा मैच यहाँ दिखेगा।','home.open.eyebrow':'सर्कल में खुला','home.open.title':'पड़ोसी अभी देख सकते हैं।','home.open.link':'सब देखें','home.open.empty':'अभी कोई खुली ज़रूरत नहीं। पहला पोस्ट करें।','home.how.eyebrow':'कैसे काम करता है','home.how.title':'चार चालें। मदद का एक साफ़ निशान।','home.how.one':'ज़रूरत पोस्ट करें','home.how.one_copy':'ट्यूशन से लेकर यात्रा तक, जो सप्ताह आसान करे उसे साझा करें।','home.how.two':'अपना ओवरलैप खोजें','home.how.two_copy':'पास के मैच कारणों के साथ दिखाई देते हैं।','home.how.three':'साथ आगे बढ़ें','home.how.three_copy':'स्वीकार, पहुँचा, भुगतान। मदद होते ही सर्कल पास आते हैं।','home.how.four':'एक निशान छोड़ें','home.how.four_copy':'OTP हैंडऑफ़ को सत्यापित करता है। पॉइंट्स और रसीद प्रभाव को दिखाते हैं।','home.ready.eyebrow':'मदद के लिए तैयार?','home.ready.title':'एक छोटे ओवरलैप से शुरू करें।','home.ready.cta':'प्रोफ़ाइल बनाएं',
      'location.title':'स्थान जोड़ें','location.subtitle':'डिवाइस निर्देशांक का उपयोग करें या क्षेत्र लिखें। ShareCircle बिना पूछे स्थान नहीं माँगता।','location.use':'मेरा स्थान उपयोग करें','location.clear':'साफ़ करें','location.area':'क्षेत्र','location.none':'कोई स्थान नहीं जोड़ा। आप फिर भी पोस्ट कर सकते हैं।','location.save':'स्थान सेव करें',
      'form.need.eyebrow':'अपने सर्कल से पूछें','form.need.title':'ज़रूरत पोस्ट करें','form.need.subtitle':'अच्छे मैच के लिए पर्याप्त स्पष्ट रहें, लेकिन मानवीय बने रहें।','form.need.submit':'ज़रूरत प्रकाशित करें','form.offer.eyebrow':'जो कर सकते हैं साझा करें','form.offer.title':'ऑफ़र पोस्ट करें','form.offer.subtitle':'आपका समय, सवारी, कौशल, सामान या खाना किसी और का दिन आसान कर सकता है।','form.offer.submit':'ऑफ़र प्रकाशित करें','form.title':'शीर्षक','form.description':'विवरण','form.category':'श्रेणी','form.urgency':'तत्कालता','form.availability':'उपलब्धता','form.price':'कीमत','form.price_hint':'इस ज़रूरत के लिए मददगार को मिलने वाली राशि तय करें। स्वीकार करने से पहले यह दिखाई जाएगी।','detail.price':'कीमत','detail.price_copy':'इस ज़रूरत के लिए मददगार को अपेक्षित भुगतान।','urgency.low':'कम','urgency.medium':'मध्यम','urgency.high':'उच्च',
      'auth.login.eyebrow':'वापसी पर स्वागत है','auth.login.title':'अपने सर्कल में लॉग इन करें।','auth.login.subtitle':'यूज़रनेम या ईमेल से लॉग इन करें।','auth.identifier':'यूज़रनेम या ईमेल','auth.password':'पासवर्ड','auth.remember':'लॉगिन याद रखें','auth.forgot':'पासवर्ड भूल गए?','auth.login.submit':'लॉग इन','auth.new_here':'नए हैं?','auth.create':'खाता बनाएं','auth.browse':'ब्राउज़ करना जारी रखें','auth.signup.eyebrow':'सर्कल में जुड़ें','auth.signup.title':'अपनी प्रोफ़ाइल बनाएं।','auth.signup.subtitle':'कुछ बुनियादी जानकारी के बाद आप पूछ और साझा कर सकते हैं।','auth.full_name':'पूरा नाम','auth.username':'यूज़रनेम','auth.username_hint':'3+ अक्षर। उपलब्धता टाइप करते समय जाँची जाती है।','auth.email':'ईमेल','auth.location':'स्थान','auth.location_hint':'इलाका या शहर चुनें, या अधिक विशिष्ट क्षेत्र लिखें।','auth.continue':'जारी रखें','auth.password_hint':'लंबा पासवर्ड बेहतर है; अक्षर, नंबर या प्रतीकों का मिश्रण रखें।','auth.back':'वापस','auth.signup.submit':'खाता बनाएं','auth.already':'पहले से जुड़े हैं?','auth.login_link':'लॉग इन','auth.forgot_title':'पासवर्ड भूल गए?','auth.forgot_copy':'अपने खाते का ईमेल दें। ShareCircle अगला उपलब्ध रिकवरी चरण दिखाएगा।','auth.forgot_submit':'रीसेट माँगें','auth.back_login':'लॉग इन पर वापस जाएँ',
      'nearby.eyebrow':'आपका स्थानीय सर्कल','nearby.title':'आपकी दूरी के भीतर की ज़रूरतें।','nearby.subtitle':'किसी सिग्नल को टैप करके ज़रूरत देखें, या सुलभ सूची का उपयोग करें।','nearby.add_offer':'एक और ऑफ़र जोड़ें','nearby.change':'बदलें','nearby.manual_hint':'मैनुअल मोड में ब्राउज़र अनुमति की ज़रूरत नहीं है।','nearby.ready':'पास की ज़रूरतें खोजने के लिए तैयार','nearby.you_offer':'आप ऑफ़र करते हैं:','nearby.offer_hint':'पास की मेल खाती ज़रूरतें देखने के लिए ऑफ़र पोस्ट करें।','nearby.list_view':'सूची','nearby.circle_view':'सर्कल फ़ील्ड',
      'match.back':'डैशबोर्ड','live.label':'लाइव','live.updated':'अभी अपडेट','match.chat_eyebrow':'मैच चैट','match.chat_title':'हैंडऑफ़ साफ़ रखें।','live.messages':'संदेश लाइव अपडेट होते हैं','match.chat_loading':'संदेश लोड हो रहे हैं…','match.send':'भेजें','match.job':'काम','match.need_owner':'ज़रूरत बताने वाला','match.helper':'हेल्पर','match.directions':'दिशा खोलें','match.safety':'सुरक्षा पहले','match.safety_copy':'सार्वजनिक जगह मिलें, अपनी यात्रा साझा करें और भुगतान विवरण निजी रखें।','match.share_trip':'यात्रा साझा करें','match.report':'रिपोर्ट / ब्लॉक',
      'dashboard.eyebrow':'आपका सर्कल','dashboard.subtitle':'अपनी ज़रूरतें आगे बढ़ाएँ और अपनी मदद को दिखाई दें।','dashboard.to_badge':'अगले बैज तक','dashboard.post_need':'ज़रूरत पोस्ट करें','dashboard.post_offer':'ऑफ़र पोस्ट करें','dashboard.nearby':'पास की ज़रूरतें','dashboard.profile':'प्रोफ़ाइल देखें','dashboard.open_match':'मैच खोलें','dashboard.needs':'मेरी ज़रूरतें','dashboard.offers':'मेरे ऑफ़र','dashboard.get_started':'शुरू करें','dashboard.build_title':'तीन चालों में अपना सर्कल बनाएं।','dashboard.step_need':'पहली ज़रूरत पोस्ट करें','dashboard.step_need_hint':'स्थानीय मदद माँगें।','dashboard.step_offer':'एक ऑफ़र जोड़ें','dashboard.step_offer_hint':'कुछ उपयोगी साझा करें।','dashboard.step_nearby':'पास में खोलें','dashboard.step_nearby_hint':'पास के लोगों को खोजें।',
      'browse.eyebrow':'सर्कल बोर्ड','browse.title':'देखें आपका पड़ोस क्या साझा कर सकता है।','browse.subtitle':'सार्वजनिक ज़रूरतें और ऑफ़र खोजें। श्रेणी और तात्कालिकता एक टैप दूर।','browse.needs':'ज़रूरतें','browse.offers':'ऑफ़र','browse.category':'श्रेणी','browse.all':'सभी','browse.urgency':'तत्कालता','browse.any':'कोई भी','browse.load_more':'और देखें',
      'impact.eyebrow':'सामुदायिक प्रभाव','impact.title':'एक पूरा मैच पड़ोस पर एक और निशान बन जाता है।','impact.subtitle':'लाइव प्लेटफ़ॉर्म आँकड़े पूरे हुए मैचों की जीवित रंगोली में दिखते हैं।','impact.completed.eyebrow':'मदद कहाँ पहुँची','impact.completed.title':'पूरे हुए मैचों की शीर्ष श्रेणियाँ','impact.completed.empty':'चार्ट जगाने के लिए अपना पहला मैच पूरा करें।','impact.rangoli.eyebrow':'समुदाय की रंगोली','impact.rangoli.title':'हर मदद एक पंखुड़ी छोड़ती है।','impact.supply.eyebrow':'मांग और उपलब्ध मदद','impact.supply.title':'जहाँ सर्कल को और हाथ चाहिए।','impact.supply.subtitle':'हर श्रेणी में खुली ज़रूरतों की तुलना उपलब्ध ऑफ़रों से।','impact.supply.empty':'लाइव गेज भरने के लिए एक ज़रूरत या ऑफ़र पोस्ट करें।',
      'receipt.back':'मैच पर वापस जाएँ','receipt.print':'प्रिंट / PDF में सेव करें','receipt.share_button':'रसीद साझा करें','receipt.eyebrow':'शेयरसर्कल · सामुदायिक प्रभाव','receipt.title':'इम्पैक्ट रसीद','receipt.match':'मैच','receipt.completed':'पूरा हुआ','receipt.need_owner':'ज़रूरत बताने वाला','receipt.helper':'हेल्पर','receipt.need':'ज़रूरत','receipt.category':'श्रेणी','receipt.amount':'दर्ज राशि','receipt.impact_points':'इम्पैक्ट पॉइंट्स','receipt.thanks':'पड़ोस की ज़रूरत को पूरे मैच में बदलने के लिए धन्यवाद।','receipt.share':'इस रसीद को सामुदायिक प्रभाव के एक सरल, ठोस रिकॉर्ड के रूप में रखें।','profile.eyebrow':'सामुदायिक सदस्य','profile.needs':'ज़रूरतें','profile.offers':'ऑफ़र','profile.activity':'गतिविधि','leaderboard.eyebrow':'दिखाई देने वाली उदारता','leaderboard.title':'इम्पैक्ट लीडर्स','leaderboard.subtitle':'पूरी हुई ShareCircle मदद से इम्पैक्ट पॉइंट्स मिलते हैं।','leaderboard.member':'सदस्य','leaderboard.location':'स्थान','leaderboard.points':'पॉइंट्स','leaderboard.rating':'रेटिंग','leaderboard.empty':'अभी कोई सदस्य नहीं',
      'detail.need_published':'ज़रूरत प्रकाशित।','detail.need_published_copy':'आपकी ज़रूरत सर्कल में लाइव है।','detail.can_help':'पास में मदद कर सकते हैं?','detail.can_help_copy':'आपका उपलब्ध ऑफ़र इस अनुरोध से मैच हो सकता है।','detail.accept':'यह ज़रूरत स्वीकार करें','detail.want_help':'मदद करना चाहते हैं?','detail.want_help_copy':'इसे स्वीकार करने के लिए लॉग इन करें।','detail.matches':'स्मार्ट मैच','detail.matches_title':'मदद करने वाले लोग','detail.matches_copy':'मैच स्कोर श्रेणी, कीवर्ड, तात्कालिकता और प्रतिष्ठा का उपयोग करता है।','detail.offer_published':'ऑफ़र प्रकाशित।','detail.offer_published_copy':'आपका कौशल अब सर्कल के लिए उपलब्ध है।','detail.explore':'ज़रूरतें देखें','detail.availability':'उपलब्धता'
    }
  };

  const localeKey = localStorage.getItem('sharecircle-locale');
  let locale = localeKey === 'hi' ? 'hi' : 'en';
  root.dataset.locale = locale;
  root.lang = locale;
  const t = key => translations[locale][key] || translations.en[key] || key;
  window.t = t;

  window.applyI18n = () => {
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-attr]').forEach(el => {
      (el.dataset.i18nAttr || '').split(',').forEach(pair => {
        const idx = pair.indexOf(':');
        if (idx < 1) return;
        el.setAttribute(pair.slice(0, idx), t(pair.slice(idx + 1)));
      });
    });
    const language = document.querySelector('[data-language-toggle]');
    if (language) {
      language.textContent = locale === 'hi' ? 'English' : 'हिंदी';
      language.setAttribute('aria-label', locale === 'hi' ? 'Switch language to English' : 'भाषा को हिंदी में बदलें');
    }
  };
  window.setLocale = next => { locale = next === 'hi' ? 'hi' : 'en'; localStorage.setItem('sharecircle-locale', locale); root.dataset.locale = locale; root.lang = locale; window.applyI18n(); };

  const savedTheme = localStorage.getItem('sharecircle-theme');
  root.dataset.theme = savedTheme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.querySelector('[data-language-toggle]')?.addEventListener('click', () => window.setLocale(locale === 'hi' ? 'en' : 'hi'));
  document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => { const next = root.dataset.theme === 'dark' ? 'light' : 'dark'; root.dataset.theme = next; localStorage.setItem('sharecircle-theme', next); });
  window.applyI18n();

  const toastRegion = document.getElementById('toastRegion');
  const removeToast = toast => { toast?.remove(); };
  document.querySelectorAll('.toast').forEach((toast, i) => setTimeout(() => removeToast(toast), 4500 + i * 150));
  window.showToast = (message, type = 'success') => {
    if (!toastRegion) return;
    const toast = document.createElement('div'); toast.className = `toast toast-${type}`; toast.textContent = message; toastRegion.appendChild(toast); setTimeout(() => removeToast(toast), 4200);
  };

  function animateCounter(element, target) {
    if (reducedMotion) { element.textContent = Number(target || 0).toLocaleString(); return; }
    const startValue = Number(String(element.textContent).replace(/,/g, '')) || 0;
    const started = performance.now();
    const tick = now => { const p = Math.min((now - started) / 650, 1); const e = 1 - Math.pow(1 - p, 3); element.textContent = Math.round(startValue + (Number(target) - startValue) * e).toLocaleString(); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  }
  document.querySelectorAll('[data-counter]').forEach(el => animateCounter(el, el.dataset.counter || 0));

  document.querySelectorAll('[data-tabs]').forEach(shell => {
    shell.querySelectorAll('.tab[data-tab]').forEach(tab => tab.addEventListener('click', () => {
      shell.querySelectorAll('.tab[data-tab]').forEach(btn => { const active = btn === tab; btn.classList.toggle('active', active); btn.setAttribute('aria-selected', String(active)); });
      shell.querySelectorAll('[data-panel]').forEach(panel => panel.classList.toggle('active', panel.dataset.panel === tab.dataset.tab));
    }));
  });

  const avatarPalette = ['#25345b','#4f764f','#c45c43','#9b7b24','#5e6782','#7b4e45'];
  const hash = value => Array.from(String(value || '')).reduce((n, ch) => ((n << 5) - n + ch.charCodeAt(0)) | 0, 0);
  document.querySelectorAll('[data-avatar]').forEach(avatar => { avatar.style.backgroundColor = avatarPalette[Math.abs(hash(avatar.dataset.avatar)) % avatarPalette.length]; });

  function makeFocusTrap(backdrop) {
    const focusable = () => [...backdrop.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), textarea:not([disabled]), select:not([disabled])')].filter(el => !el.hidden && el.offsetParent !== null);
    const first = () => focusable()[0];
    const onKey = event => {
      if (event.key === 'Escape') { event.preventDefault(); window.closeModal?.(backdrop); return; }
      if (event.key !== 'Tab') return;
      const nodes = focusable(); if (!nodes.length) return;
      const idx = nodes.indexOf(document.activeElement);
      if (event.shiftKey && (idx <= 0 || idx === -1)) { event.preventDefault(); nodes[nodes.length - 1].focus(); }
      else if (!event.shiftKey && idx === nodes.length - 1) { event.preventDefault(); nodes[0].focus(); }
    };
    backdrop.addEventListener('keydown', onKey);
    return { first };
  }

  const triggers = new WeakMap();
  window.openModal = (backdrop, returnFocus = document.activeElement) => {
    if (!backdrop) return;
    triggers.set(backdrop, returnFocus);
    backdrop.hidden = false;
    document.body.classList.add('modal-open');
    const trap = makeFocusTrap(backdrop); window._scModalTraps ??= new WeakMap(); window._scModalTraps.set(backdrop, trap); setTimeout(() => trap.first()?.focus(), 0);
  };
  window.closeModal = backdrop => {
    if (!backdrop) return;
    backdrop.hidden = true;
    if (!document.querySelector('.modal-backdrop:not([hidden])')) document.body.classList.remove('modal-open');
    triggers.get(backdrop)?.focus?.();
  };

  const postSheet = document.getElementById('postSheet');
  document.querySelectorAll('[data-open-post-sheet]').forEach(button => button.addEventListener('click', () => window.openModal(postSheet, button)));
  postSheet?.addEventListener('click', event => { if (event.target === postSheet) window.closeModal(postSheet); });
  postSheet?.querySelectorAll('[data-close-modal]').forEach(btn => btn.addEventListener('click', () => window.closeModal(postSheet)));

  const hackathonSheet = document.getElementById('hackathonSheet');
  const hackathonList = document.getElementById('hackathonAccountList');
  const hackathonCreateBtn = document.getElementById('hackathonCreateBtn');
  const hackathonTrigger = document.getElementById('hackathonUtilitiesBtn');
  const hackathonText = value => escapeHtml(value || '');
  async function loadHackathonAccounts() {
    if (!hackathonList) return;
    hackathonList.innerHTML = '<div class="hackathon-loading"><span class="skeleton skeleton-line"></span><span class="skeleton skeleton-line"></span></div>';
    const response = await fetch('/api/hackathon/accounts', { headers: { 'Accept': 'application/json' } }).catch(() => null);
    if (!response?.ok) { hackathonList.innerHTML = '<p class="muted">Hackathon Utilities are unavailable.</p>'; return; }
    const data = await response.json();
    const accounts = data.accounts || [];
    if (!accounts.length) {
      hackathonList.innerHTML = `<div class="hackathon-empty"><svg class="ui-icon" aria-hidden="true"><use href="#icon-toolbox"></use></svg><p>${hackathonText(locale === 'hi' ? 'अभी कोई क्विक अकाउंट नहीं है। ऊपर वाला बटन दबाएँ।' : 'No quick accounts yet. Create one above.')}</p></div>`;
      return;
    }
    const currentId = Number(document.body.dataset.userId || 0);
    hackathonList.innerHTML = accounts.map(account => {
      const active = Number(account.id) === currentId;
      return `<div class="hackathon-account${active ? ' is-current' : ''}">
        <div class="hackathon-account-avatar" aria-hidden="true">${hackathonText((account.full_name || 'J').slice(0,1))}</div>
        <div class="hackathon-account-info"><strong>${hackathonText(account.full_name)}</strong><span>@${hackathonText(account.username)}</span><small>${hackathonText(account.location)}</small></div>
        <div class="hackathon-account-actions">
          ${active ? `<span class="hackathon-current" data-i18n="hackathon.current">Current</span>` : `<button class="btn btn-secondary btn-small" type="button" data-hackathon-switch="${Number(account.id)}">${hackathonText(locale === 'hi' ? 'बदलें' : 'Switch')}</button>`}
          <button class="icon-btn hackathon-delete" type="button" data-hackathon-delete="${Number(account.id)}" aria-label="Delete quick account" title="Delete quick account"><svg class="ui-icon" aria-hidden="true"><use href="#icon-x"></use></svg></button>
        </div>
      </div>`;
    }).join('');
    hackathonList.querySelectorAll('[data-hackathon-switch]').forEach(button => button.addEventListener('click', async () => {
      button.disabled = true;
      const response = await fetch(`/api/hackathon/accounts/${button.dataset.hackathonSwitch}/switch`, { method: 'POST', headers: { 'Accept': 'application/json' } }).catch(() => null);
      if (response?.ok) window.location.reload(); else button.disabled = false;
    }));
    const deleteModal = document.getElementById('hackathonDeleteConfirm');
    const deleteConfirmBtn = document.getElementById('hackathonDeleteConfirmBtn');
    hackathonList.querySelectorAll('[data-hackathon-delete]').forEach(button => button.addEventListener('click', () => {
      if (!deleteModal || !deleteConfirmBtn) return;
      deleteConfirmBtn.dataset.userId = button.dataset.hackathonDelete;
      window.openModal(deleteModal, button);
    }));
  }
  hackathonTrigger?.addEventListener('click', () => { window.openModal(hackathonSheet, hackathonTrigger); loadHackathonAccounts(); });
  hackathonSheet?.addEventListener('click', event => { if (event.target === hackathonSheet) window.closeModal(hackathonSheet); });
  hackathonSheet?.querySelectorAll('[data-close-modal]').forEach(btn => btn.addEventListener('click', () => window.closeModal(hackathonSheet)));
  const hackathonDeleteModal = document.getElementById('hackathonDeleteConfirm');
  const hackathonDeleteConfirmBtn = document.getElementById('hackathonDeleteConfirmBtn');
  hackathonDeleteModal?.addEventListener('click', event => { if (event.target === hackathonDeleteModal) window.closeModal(hackathonDeleteModal); });
  hackathonDeleteModal?.querySelectorAll('[data-close-modal]').forEach(btn => btn.addEventListener('click', () => window.closeModal(hackathonDeleteModal)));
  hackathonDeleteConfirmBtn?.addEventListener('click', async () => {
    const userId = hackathonDeleteConfirmBtn.dataset.userId;
    if (!userId) return;
    hackathonDeleteConfirmBtn.disabled = true;
    const response = await fetch(`/api/hackathon/accounts/${userId}/delete`, { method: 'POST', headers: { 'Accept': 'application/json' } }).catch(() => null);
    if (response?.ok) window.location.reload(); else hackathonDeleteConfirmBtn.disabled = false;
  });
  hackathonCreateBtn?.addEventListener('click', async () => {
    hackathonCreateBtn.disabled = true;
    const response = await fetch('/api/hackathon/accounts', { method: 'POST', headers: { 'Accept': 'application/json' } }).catch(() => null);
    if (response?.ok) window.location.reload(); else hackathonCreateBtn.disabled = false;
  });

  const notificationBtn = document.getElementById('notificationBtn');
  const notificationMenu = document.getElementById('notificationMenu');
  const notificationBadge = document.getElementById('notificationBadge');
  async function loadNotifications() {
    if (!notificationMenu) return;
    const response = await fetch('/api/notifications').catch(() => null); if (!response?.ok) return;
    const data = await response.json();
    const items = data.items || [];
    notificationMenu.innerHTML = items.length ? items.map(item => `<a class="notification-item" href="${String(item.link || '#').replace(/"/g, '&quot;')}"><p>${escapeHtml(item.body)}</p><small>${relativeTime(item.created_at)}</small></a>`).join('') : `<div class="notification-item"><p>${escapeHtml(locale === 'hi' ? 'अभी कोई नई सूचना नहीं।' : 'No notifications yet.')}</p></div>`;
    if (notificationBadge) { notificationBadge.textContent = String(data.unread || 0); notificationBadge.classList.toggle('hidden', !data.unread); }
  }
  function escapeHtml(v) { return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
  function relativeTime(value) { if (!value) return 'recently'; const d = new Date(String(value).replace(' ','T')+'Z'); if (Number.isNaN(d.getTime())) return 'recently'; const s = Math.max(0, Math.floor((Date.now()-d.getTime())/1000)); if(s<60)return 'just now';const m=Math.floor(s/60);if(m<60)return `${m}m ago`;const h=Math.floor(m/60);if(h<24)return `${h}h ago`;return `${Math.floor(h/24)}d ago`; }
  notificationBtn?.addEventListener('click', async () => {
    const open = notificationMenu.hidden; notificationMenu.hidden = !open; notificationBtn.setAttribute('aria-expanded', String(open));
    if (open) { await loadNotifications(); const r = await fetch('/api/notifications/read',{method:'POST'}).catch(()=>null); if(r?.ok && notificationBadge){notificationBadge.classList.add('hidden');} }
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.notification-wrap') && notificationMenu && !notificationMenu.hidden) { notificationMenu.hidden = true; notificationBtn?.setAttribute('aria-expanded','false'); }
    document.querySelectorAll('.card-menu-pop').forEach(menu => { if (!event.target.closest('.card-menu')) menu.hidden = true; });
  });

  if (document.getElementById('homeStats')) {
    const refresh = async () => { const r = await fetch('/api/stats').catch(()=>null); if(!r?.ok)return;const data=await r.json();document.querySelectorAll('#homeStats [data-stat]').forEach(el=>{el.dataset.counter=data[el.dataset.stat]??0;animateCounter(el,el.dataset.counter)}); };
    setInterval(refresh, 7000);
  }
})();
(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp = (n,a,b) => Math.max(a, Math.min(b,n));
  const makeCanvasScene = canvas => {
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    const host = canvas.parentElement;
    let width = 0, height = 0, dpr = 1, running = true, raf = 0;
    const dots = [], ripples = [];
    const maxDots = 38, maxRipples = reducedMotion ? 2 : 5;
    const resize = () => {
      const box = host.getBoundingClientRect(); dpr = Math.min(window.devicePixelRatio || 1, 1.5); width = Math.max(1, Math.floor(box.width)); height = Math.max(1, Math.floor(box.height)); canvas.width = Math.floor(width*dpr); canvas.height = Math.floor(height*dpr); ctx.setTransform(dpr,0,0,dpr,0,0);
      while(dots.length<maxDots){dots.push({x:.08+Math.random()*.84,y:.12+Math.random()*.76,r:Math.random()<.12?3.2:2.1,lit:0});}
    };
    const drop = (x,y) => {
      for(let i=0;i<maxRipples;i++){
        if(ripples.length>=maxRipples) ripples.shift();
        ripples.push({x,y,r:i*22,alpha:0.65/(i+1),speed:reducedMotion?0.9:3.2-i*.35});
      }
    };
    const pointer = event => { const rect=canvas.getBoundingClientRect(); drop(event.clientX-rect.left,event.clientY-rect.top); };
    canvas.addEventListener('pointerdown', pointer); canvas.addEventListener('pointermove', event => { if(event.buttons) pointer(event); });
    let lastAuto=0;
    const draw = now => {
      if(!running) { raf=requestAnimationFrame(draw); return; }
      ctx.clearRect(0,0,width,height);
      dots.forEach(dot=>{dot.lit*=.88; const x=dot.x*width,y=dot.y*height; ctx.beginPath();ctx.arc(x,y,dot.r+dot.lit*2.5,0,Math.PI*2);ctx.fillStyle=dot.lit>.1?'#f0b53d':'rgba(246,240,229,.45)';ctx.fill();});
      ripples.forEach(r=>{r.r+=r.speed;r.alpha*=.994;ctx.beginPath();ctx.arc(r.x,r.y,r.r,0,Math.PI*2);ctx.strokeStyle=`rgba(240,181,61,${r.alpha})`;ctx.lineWidth=1.4;ctx.stroke();dots.forEach(dot=>{const dx=dot.x*width-r.x,dy=dot.y*height-r.y;if(Math.abs(Math.hypot(dx,dy)-r.r)<4)dot.lit=1;});});
      for(let i=ripples.length-1;i>=0;i--)if(ripples[i].r>Math.max(width,height)*.85||ripples[i].alpha<.03)ripples.splice(i,1);
      if(now-lastAuto>2600&&!reducedMotion){drop(width*.5,height*.5);lastAuto=now;}
      raf=requestAnimationFrame(draw);
    };
    const observer = new IntersectionObserver(entries => { running=entries[0]?.isIntersecting !== false && !document.hidden; }); observer.observe(host);
    document.addEventListener('visibilitychange',()=>{running=!document.hidden;});
    resize(); window.addEventListener('resize',resize,{passive:true}); raf=requestAnimationFrame(draw);
    return {drop:()=>drop(width*.5,height*.5), destroy:()=>cancelAnimationFrame(raf)};
  };

  const canvas = document.getElementById('heroRippleCanvas');
  if(canvas) makeCanvasScene(canvas);

  window.ShareCircleRipple = {
    submitPulse: async target => {
      if (reducedMotion) return;
      const overlay=document.createElement('div'); overlay.className='ripple-overlay'; overlay.setAttribute('aria-hidden','true'); overlay.innerHTML='<svg viewBox="0 0 100 100" preserveAspectRatio="none"><circle cx="50" cy="50" r="4"></circle><circle cx="50" cy="50" r="8"></circle><circle cx="50" cy="50" r="14"></circle></svg>'; document.body.appendChild(overlay);
      const circles=[...overlay.querySelectorAll('circle')]; const duration=760;
      await Promise.all(circles.map((c,i)=>new Promise(resolve=>{c.animate([{r:'4',opacity:.65},{r:'80',opacity:0}],{duration:duration+i*80,easing:'cubic-bezier(.16,1,.3,1)',fill:'forwards'}).onfinish=resolve;})));
      overlay.remove();
    }
  };
})();
(() => {
  const svg = document.getElementById('impactRangoli');
  if (!svg) return;
  const completed = Math.max(0, Number(document.body.dataset.completedMatches || svg.dataset.completed || 0));
  const countFromCaption = Number((document.getElementById('rangoliCaption')?.textContent.match(/^\s*(\d+)/) || [0,0])[1]);
  const matchCount = completed || countFromCaption || 0;
  const NS = 'http://www.w3.org/2000/svg';
  const center = 250;
  const petals = Math.min(72, Math.max(8, matchCount * 2));
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const make = (tag, attrs = {}) => {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  };

  function build() {
    svg.innerHTML = '';
    const bg = make('circle', {cx:center, cy:center, r:218, fill:'none', stroke:'currentColor', 'stroke-opacity':'.12'});
    svg.appendChild(bg);
    for (let i = 0; i < 12; i += 1) {
      const r = 78 + (i % 3) * 36;
      const angle = (Math.PI * 2 * i) / 12;
      svg.appendChild(make('circle', {cx:center + Math.cos(angle)*r, cy:center + Math.sin(angle)*r, r:3.4, fill:i % 2 ? '#E2A62B' : '#C45C43', 'fill-opacity':'.72'}));
    }
    if (!matchCount) return;
    for (let i = 0; i < petals; i += 1) {
      const angle = (Math.PI * 2 * i) / petals;
      const radius = 72 + (i % 4) * 28;
      const x = center + Math.cos(angle) * radius;
      const y = center + Math.sin(angle) * radius;
      const group = make('g', {class:'rangoli-petal'});
      group.style.animationDelay = `${Math.min(i * 24, 900)}ms`;
      const petal = make('ellipse', {cx:x, cy:y, rx:7 + (i % 3), ry:18 + (i % 4) * 2, fill:i % 3 === 0 ? '#E2A62B' : i % 3 === 1 ? '#C45C43' : '#4F764F', 'fill-opacity':'.74', transform:`rotate(${angle * 180 / Math.PI} ${x} ${y})`});
      group.appendChild(petal);
      svg.appendChild(group);
    }
    const inner = make('circle', {cx:center, cy:center, r:28, fill:'#17213A'});
    const innerText = make('text', {x:center, y:center + 5, 'text-anchor':'middle', fill:'#F6F0E5', 'font-family':'DM Sans, sans-serif', 'font-size':'13', 'font-weight':'800'});
    innerText.textContent = `${matchCount}`;
    svg.appendChild(inner);
    svg.appendChild(innerText);
  }

  build();
  if (!prefersReduced) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) build();
    }, {threshold:.2});
    observer.observe(svg);
  }
})();
(() => {
  const button = document.getElementById('shareReceipt');
  const receipt = document.getElementById('impactReceipt');
  if (!button || !receipt) return;
  const title = receipt.querySelector('h1')?.textContent?.trim() || 'ShareCircle Impact Receipt';
  const text = receipt.innerText.replace(/\n{3,}/g, '\n\n').trim();
  button.addEventListener('click', async () => {
    try {
      if (navigator.share) {
        await navigator.share({title, text, url:button.dataset.shareUrl || window.location.href});
        return;
      }
      await navigator.clipboard.writeText(`${text}\n\n${button.dataset.shareUrl || window.location.href}`);
      window.showToast?.('Receipt copied. Paste it into a message.', 'success');
    } catch (_) {
      window.showToast?.('Sharing was cancelled.', 'error');
    }
  });
})();
