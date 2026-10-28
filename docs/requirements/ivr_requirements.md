# Phone requirements

These are the requirements for the finished phone channel. Each item must hold. If one item does not happen, the channel does not work.

The person can ask in their own words. The channel can do five things: give the balance, give the PIN, give a statement, block the card, and unblock the card. It does not do anything else.

1. The channel is available every day, at every hour.
2. A call from a number that is not a customer's number is refused before any language choice. The call ends. The system does not ask for a language, does not ask for card digits, and does not give any account information.
3. A withheld number, or a call with no number, is refused in the same way. The spoken line is "This number is not recognised."
4. The refusal is spoken in the first language of the caller's country when that language is French, Hebrew, or Arabic. Every other refusal is spoken in English.
5. The French refusal is "Ce numéro n'est pas reconnu."
6. The Hebrew refusal is "המספר הזה אינו מזוהה."
7. The Arabic refusal is "هذا الرقم غير معروف."
8. The English refusal is "This number is not recognised."
9. A customer is asked, once, which language to use for the rest of the call. The question asks them to say the name of the language they want. It is spoken in the first language of their country. If that language cannot be spoken, the question is the English line "Please say the name of the language you would like to use."
10. Where the question language has a fixed line, that line is exact:
    - Amharic: "እባክዎ የሚፈልጉትን ቋንቋ ስም ይናገሩ።"
    - Arabic: "من فضلك قل اسم اللغة التي تريد استخدامها."
    - Bengali: "অনুগ্রহ করে যে ভাষাটি ব্যবহার করতে চান তার নাম বলুন।"
    - German: "Bitte sagen Sie den Namen der Sprache, die Sie verwenden möchten."
    - Greek: "Παρακαλώ πείτε το όνομα της γλώσσας που θέλετε να χρησιμοποιήσετε."
    - English: "Please say the name of the language you would like to use."
    - Spanish: "Por favor, diga el nombre del idioma que desea usar."
    - Persian: "لطفاً نام زبانی را که می‌خواهید استفاده کنید بگویید."
    - French: "Veuillez dire le nom de la langue que vous souhaitez utiliser."
    - Hebrew: "אנא אמור את שם השפה שבה תרצה להשתמש."
    - Hindi: "कृपया उस भाषा का नाम बोलें जिसका आप उपयोग करना चाहते हैं।"
    - Indonesian: "Silakan sebutkan nama bahasa yang ingin Anda gunakan."
    - Italian: "Per favore, dica il nome della lingua che desidera usare."
    - Japanese: "ご利用になりたい言語の名前を話してください。"
    - Korean: "사용하실 언어의 이름을 말씀해 주세요."
    - Dutch: "Zeg alstublieft de naam van de taal die u wilt gebruiken."
    - Polish: "Proszę powiedzieć nazwę języka, którego chcesz używać."
    - Portuguese: "Por favor, diga o nome do idioma que deseja usar."
    - Russian: "Пожалуйста, скажите название языка, который вы хотите использовать."
    - Swahili: "Tafadhali sema jina la lugha unayotaka kutumia."
    - Thai: "กรุณาพูดชื่อภาษาที่คุณต้องการใช้"
    - Turkish: "Lütfen kullanmak istediğiniz dilin adını söyleyin."
    - Ukrainian: "Будь ласка, назвіть мову, якою ви хочете користуватися."
    - Urdu: "براہ کرم اس زبان کا نام بتائیں جو آپ استعمال کرنا چاہتے ہیں۔"
    - Vietnamese: "Vui lòng nói tên ngôn ngữ bạn muốn sử dụng."
    - Chinese: "请说出您想使用的语言名称。"
11. Saying one language name selects that language. The name may be the English name or the name of the language in that language. Two different language names in one answer do not select a language.
12. If they do not choose, the system offers the keypad. The introduction means "if you prefer to use the keypad, press the number for your language", spoken in the same language as the question. The exact introduction is:
    - English: "If you prefer to use the keypad, press the number for your language."
    - Spanish: "Si prefiere usar el teclado, pulse el número de su idioma."
    - French: "Si vous préférez utiliser le clavier, appuyez sur le numéro de votre langue."
    - Hebrew: "אם תרצה להשתמש במקלדת, הקש את המספר של השפה שלך."
    - Arabic: "إذا كنت تفضل استخدام لوحة المفاتيح، اضغط على رقم لغتك."
13. Each keypad choice is spoken as "For" plus the English name of the language, plus "press" and the digit. The digit order is the order for that country, listed below. A digit that is not on the list does nothing.
14. They may say a language name during the keypad. That choice is kept, and the keypad stops.
15. If they still do not choose after the keypad has been offered twice, the call ends. The system does not ask for card digits and does not give any account information.
16. A customer whose country is not known is asked in English and offered this keypad: 1 English, 2 Spanish, 3 French, 4 Arabic, 5 Chinese, 6 Hindi, 7 Portuguese.
17. After a language is chosen, every later question and answer on that call is in that language. The system does not ask for a language again, even if the person later speaks a different language.
18. Before any balance, PIN, statement, block, or unblock, the person must give the last 4 digits of the card. The system asks once per call. A later request on the same call does not ask again.
19. They may speak the four digits or enter them on the keypad. If they say nothing while those digits are being asked for, the system offers the keypad. It does not treat that silence as a misunderstood request.
20. A wrong last 4 gives no account information and makes no change to the card. They may try once more. A second wrong last 4 ends the call.
21. If the person has one card, the system uses that card and does not ask which card it is.
22. If the person has more than one card, the system asks which card before it acts, unless the person has already identified one. They may name the card or give its last 4 digits. A last 4 that matches one of their cards both chooses that card and satisfies the check. A last 4 that matches none of their cards is a wrong last 4.
23. After the check has passed, the person can make several requests in the same call, in their own words. They can correct a request that has not yet been carried out. A correction replaces the pending request. It is not counted as a misunderstood request.
24. If they ask for more than one of the five actions in one turn, the system handles them one at a time, in the order they asked. It finishes or confirms one before it starts the next.
25. The system does not guess. A request it does not understand, or a request that is not one of the five actions, is declined. The reply names the five things it can do: balance, PIN, statement, block, and unblock. They get two such failures, then the call ends.
26. Silence while the system is waiting for a request makes it ask again what they need. A second silence ends the call, with no action taken. Silence does not count as one of the two misunderstood requests.
27. A balance reply contains the amount, the currency, and the date and time that amount is true for. The amount is the real balance of the chosen card. Balance does not wait for a yes.
28. A PIN reply contains the real PIN of the chosen card. It contains no other card's PIN. The PIN does not wait for a yes. A later reply does not include the PIN again unless they ask for it again.
29. A statement reply contains the statement period and the closing balance for that period. It does not have to list every transaction. If they name a period, that period is used. If they do not name a period, the latest statement is used, and the reply says which period it is. If they name a period that has no statement, the system says so and asks for another period. That question is not a misunderstood request. A statement does not wait for a yes.
30. Block and unblock change the card. The system asks for a clear yes before it changes anything. A clear no cancels the change. The card stays as it was, and they can ask for something else.
31. They may answer yes or no by speaking, or by keypad. Keypad 1 means yes. Keypad 2 means no. Any other digit does nothing. If they say nothing while yes or no is being asked for, the system offers that keypad.
32. An unclear answer to yes or no asks the same question once more. A second unclear answer cancels the change. The card is not changed. This does not count as one of the two misunderstood requests.
33. After a yes, a block leaves the card blocked, and the person is told that it is blocked. An unblock leaves the card unblocked, and the person is told that it is unblocked. The change is real.
34. If the card is already blocked, the system says so and does not ask for a yes to block it again. If the card is already unblocked, the system says so and does not ask for a yes to unblock it again.
35. Until they say yes, they can replace a pending block or unblock with a different request. The cancelled change does not happen.
36. The system does not keep a recording of the call.

Keypad languages, in digit order:

- Afghanistan: 1 Pashto, 2 Persian, 3 Uzbek, 4 English
- Albania: 1 Albanian, 2 English
- Algeria: 1 Arabic, 2 French, 3 English
- Argentina: 1 Spanish, 2 English
- Armenia: 1 Armenian, 2 Russian, 3 English
- Australia: 1 English, 2 Chinese, 3 Arabic, 4 Vietnamese
- Austria: 1 German, 2 English
- Azerbaijan: 1 Azerbaijani, 2 Russian, 3 English
- Bahrain: 1 Arabic, 2 English
- Bangladesh: 1 Bengali, 2 English
- Belarus: 1 Belarusian, 2 Russian, 3 English
- Belgium: 1 Dutch, 2 French, 3 German, 4 English
- Benin: 1 French, 2 Yoruba, 3 English
- Bolivia: 1 Spanish, 2 Quechua, 3 Aymara, 4 English
- Bosnia and Herzegovina: 1 Bosnian, 2 Croatian, 3 Serbian, 4 English
- Botswana: 1 English, 2 Tswana
- Brazil: 1 Portuguese, 2 Spanish, 3 English
- Bulgaria: 1 Bulgarian, 2 English, 3 Turkish
- Burundi: 1 Kirundi, 2 French, 3 English, 4 Swahili
- Cambodia: 1 Khmer, 2 English
- Cameroon: 1 French, 2 English
- Canada: 1 English, 2 French
- Central African Republic: 1 French, 2 Sango, 3 English
- Chad: 1 French, 2 Arabic, 3 English
- Chile: 1 Spanish, 2 English
- China: 1 Chinese, 2 English
- Colombia: 1 Spanish, 2 English
- Congo: 1 French, 2 Lingala, 3 English
- Costa Rica: 1 Spanish, 2 English
- Côte d'Ivoire: 1 French, 2 English
- Croatia: 1 Croatian, 2 English
- Cuba: 1 Spanish, 2 English
- Cyprus: 1 Greek, 2 Turkish, 3 English
- Czechia: 1 Czech, 2 English, 3 Slovak
- Democratic Republic of the Congo: 1 French, 2 Swahili, 3 Lingala, 4 English
- Denmark: 1 Danish, 2 English
- Djibouti: 1 French, 2 Arabic, 3 English, 4 Somali
- Dominican Republic: 1 Spanish, 2 English
- Ecuador: 1 Spanish, 2 English, 3 Quechua
- Egypt: 1 Arabic, 2 English
- El Salvador: 1 Spanish, 2 English
- Equatorial Guinea: 1 Spanish, 2 French, 3 Portuguese, 4 English
- Eritrea: 1 Tigrinya, 2 Arabic, 3 English
- Eswatini: 1 English, 2 Swati
- Estonia: 1 Estonian, 2 Russian, 3 English
- Ethiopia: 1 Amharic, 2 Oromo, 3 Somali, 4 English
- Finland: 1 Finnish, 2 Swedish, 3 English
- France: 1 French, 2 English, 3 Arabic
- Gabon: 1 French, 2 English
- Gambia: 1 English, 2 Wolof
- Georgia: 1 Georgian, 2 Russian, 3 English
- Germany: 1 German, 2 English, 3 Turkish, 4 Russian
- Ghana: 1 English, 2 Akan, 3 Ewe
- Greece: 1 Greek, 2 English
- Guatemala: 1 Spanish, 2 English
- Guinea: 1 French, 2 English
- Haiti: 1 Haitian Creole, 2 French, 3 English
- Honduras: 1 Spanish, 2 English
- Hong Kong: 1 Chinese, 2 English
- Hungary: 1 Hungarian, 2 English
- Iceland: 1 Icelandic, 2 English
- India: 1 Hindi, 2 English, 3 Bengali, 4 Telugu, 5 Marathi, 6 Tamil, 7 Urdu
- Indonesia: 1 Indonesian, 2 English, 3 Javanese
- Iran: 1 Persian, 2 Azerbaijani, 3 Kurdish, 4 English
- Iraq: 1 Arabic, 2 Kurdish, 3 English
- Ireland: 1 English, 2 Irish, 3 Polish
- Israel: 1 Hebrew, 2 Arabic, 3 English, 4 Russian
- Italy: 1 Italian, 2 English, 3 German, 4 French
- Japan: 1 Japanese, 2 English
- Jordan: 1 Arabic, 2 English
- Kazakhstan: 1 Kazakh, 2 Russian, 3 English
- Kenya: 1 Swahili, 2 English
- Kosovo: 1 Albanian, 2 Serbian, 3 English
- Kuwait: 1 Arabic, 2 English
- Kyrgyzstan: 1 Kyrgyz, 2 Russian, 3 English
- Laos: 1 Lao, 2 English
- Lebanon: 1 Arabic, 2 French, 3 English
- Lesotho: 1 Sesotho, 2 English, 3 Zulu
- Liberia: 1 English
- Libya: 1 Arabic, 2 English
- Lithuania: 1 Lithuanian, 2 Russian, 3 English
- Luxembourg: 1 French, 2 German, 3 Luxembourgish, 4 English
- Madagascar: 1 Malagasy, 2 French, 3 English
- Malawi: 1 English, 2 Chichewa
- Malaysia: 1 Malay, 2 English, 3 Chinese, 4 Tamil
- Mali: 1 French, 2 Bambara, 3 English
- Malta: 1 Maltese, 2 English
- Mauritania: 1 Arabic, 2 French, 3 English
- Mexico: 1 Spanish, 2 English
- Moldova: 1 Romanian, 2 Russian, 3 English
- Mongolia: 1 Mongolian, 2 English
- Montenegro: 1 Serbian, 2 English
- Morocco: 1 Arabic, 2 French, 3 English, 4 Berber
- Mozambique: 1 Portuguese, 2 English, 3 Swahili
- Myanmar: 1 Burmese, 2 English
- Namibia: 1 English, 2 Afrikaans, 3 German
- Nepal: 1 Nepali, 2 English
- Netherlands: 1 Dutch, 2 English
- New Zealand: 1 English, 2 Maori
- Nicaragua: 1 Spanish, 2 English
- Niger: 1 French, 2 Hausa, 3 English
- Nigeria: 1 English, 2 Hausa, 3 Yoruba, 4 Igbo
- North Macedonia: 1 Macedonian, 2 Albanian, 3 English
- Norway: 1 Norwegian, 2 English
- Oman: 1 Arabic, 2 English
- Pakistan: 1 Urdu, 2 English, 3 Punjabi, 4 Pashto
- Palestine: 1 Arabic, 2 English, 3 Hebrew
- Panama: 1 Spanish, 2 English
- Paraguay: 1 Spanish, 2 Guarani, 3 English
- Peru: 1 Spanish, 2 Quechua, 3 English
- Philippines: 1 English, 2 Filipino, 3 Cebuano
- Poland: 1 Polish, 2 English
- Portugal: 1 Portuguese, 2 English
- Qatar: 1 Arabic, 2 English, 3 Hindi
- Romania: 1 Romanian, 2 English, 3 Hungarian
- Russia: 1 Russian, 2 English, 3 Tatar
- Rwanda: 1 Kinyarwanda, 2 English, 3 French, 4 Swahili
- Saudi Arabia: 1 Arabic, 2 English
- Senegal: 1 French, 2 Wolof, 3 English
- Serbia: 1 Serbian, 2 English, 3 Hungarian
- Sierra Leone: 1 English
- Singapore: 1 English, 2 Chinese, 3 Malay, 4 Tamil
- Slovakia: 1 Slovak, 2 English, 3 Hungarian
- Slovenia: 1 Slovenian, 2 English
- Somalia: 1 Somali, 2 Arabic, 3 English
- South Africa: 1 English, 2 Zulu, 3 Xhosa, 4 Afrikaans, 5 Sesotho
- South Korea: 1 Korean, 2 English
- South Sudan: 1 English, 2 Arabic
- Spain: 1 Spanish, 2 Catalan, 3 Galician, 4 Basque, 5 English
- Sri Lanka: 1 Sinhala, 2 Tamil, 3 English
- Sudan: 1 Arabic, 2 English
- Sweden: 1 Swedish, 2 English, 3 Arabic
- Switzerland: 1 German, 2 French, 3 Italian, 4 English
- Syria: 1 Arabic, 2 Kurdish, 3 English
- Tajikistan: 1 Tajik, 2 Russian, 3 English
- Tanzania: 1 Swahili, 2 English
- Thailand: 1 Thai, 2 English
- Timor-Leste: 1 Portuguese, 2 Tetum, 3 English
- Togo: 1 French, 2 Ewe, 3 English
- Tunisia: 1 Arabic, 2 French, 3 English
- Turkey: 1 Turkish, 2 Kurdish, 3 English, 4 Arabic
- Turkmenistan: 1 Turkmen, 2 Russian, 3 English
- Uganda: 1 English, 2 Swahili
- Ukraine: 1 Ukrainian, 2 Russian, 3 English
- United Arab Emirates: 1 Arabic, 2 English, 3 Hindi, 4 Urdu
- United Kingdom: 1 English, 2 Polish, 3 Punjabi, 4 Urdu, 5 Bengali
- United States: 1 English, 2 Spanish, 3 Chinese, 4 French
- Uruguay: 1 Spanish, 2 English
- Uzbekistan: 1 Uzbek, 2 Russian, 3 English
- Venezuela: 1 Spanish, 2 English
- Vietnam: 1 Vietnamese, 2 English
- Yemen: 1 Arabic, 2 English
- Zambia: 1 English, 2 Chichewa, 3 Bemba
- Zimbabwe: 1 English, 2 Shona, 3 Northern Ndebele
