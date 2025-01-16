import re
import execjs
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import asyncio
import googletrans

class TkGenerator:
    """
    Compute the "TK" of the string.
    TK is a str generated by js, and you should post the string and the corresponding TK when you translate.
    Just like the hash of a string.
    """

    def __init__(self):
        self.ctx = execjs.compile("""
        function TL(a) {
        var k = "";
        var b = 406644;
        var b1 = 3293161072;
        var jd = ".";
        var $b = "+-a^+6";
        var Zb = "+-3^+b+-f";
        for (var e = [], f = 0, g = 0; g < a.length; g++) {
            var m = a.charCodeAt(g);
            128 > m ? e[f++] = m : (2048 > m ? e[f++] = m >> 6 | 192 : (55296 == (m & 64512) && g + 1 < a.length && 56320 == (a.charCodeAt(g + 1) & 64512) ? (m = 65536 + ((m & 1023) << 10) + (a.charCodeAt(++g) & 1023),
            e[f++] = m >> 18 | 240,
            e[f++] = m >> 12 & 63 | 128) : e[f++] = m >> 12 | 224,
            e[f++] = m >> 6 & 63 | 128),
            e[f++] = m & 63 | 128)
        }
        a = b;
        for (f = 0; f < e.length; f++) a += e[f],
        a = RL(a, $b);
        a = RL(a, Zb);
        a ^= b1 || 0;
        0 > a && (a = (a & 2147483647) + 2147483648);
        a %= 1E6;
        return a.toString() + jd + (a ^ b)
    };
    function RL(a, b) {
        var t = "a";
        var Yb = "+";
        for (var c = 0; c < b.length - 2; c += 3) {
            var d = b.charAt(c + 2),
            d = d >= t ? d.charCodeAt(0) - 87 : Number(d),
            d = b.charAt(c + 1) == Yb ? a >>> d: a << d;
            a = b.charAt(c) == Yb ? a + d & 4294967295 : a ^ d
        }
        return a
    }
    """)

    def get_tk(self, text: str) -> str:
        return self.ctx.call("TL", text)


class Translator:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        self.tk_gen = TkGenerator()
        self.pattern = re.compile(r'\["(.*?)(?:\\n)')
        self.max_limited = 3500
        self.google_translator = googletrans.Translator()
        self.translated_list = []

    def __post(self, url, text):
        post_data = {
            'q': text
        }
        data = urllib.parse.urlencode(post_data).encode(encoding='utf-8')
        request = urllib.request.Request(url=url, data=data, headers=self.headers)
        response = urllib.request.urlopen(request)
        return response.read().decode('utf-8')

    def __translate(self, text, src_lang, target_lang) -> str:
        tk = self.tk_gen.get_tk(text)
        url = "https://translate.google.com.tw/translate_a/single?client=t" \
              "&sl=%s&tl=%s&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca" \
              "&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&clearbtn=1&otf=1&pc=1" \
              "&srcrom=0&ssel=0&tsel=0&kc=1&tk=%s" % (src_lang, target_lang, tk)

        result = self.__post(url, text)
        return result

    def translate_raw(self, text: str, src_lang: str, target_lang: str) -> str:
        """
        Similar with the method "translate", but this return more information.
        :param text: Origin text
        :param src_lang: source language. the ISO-639-1 language code of the input text
        :param target_lang: target language. the ISO-639-1 language code of the output text
        :return: raw respond string
        """
        return self.__translate(text, src_lang, target_lang)

    def translate(self, text: str, src_lang: str, target_lang: str) -> str:
        """
        Execute translate.
        Afrikaans	af      Albanian	sq      Amharic	am      Arabic	ar      Armenian	hy      Azerbaijani	az
        Basque	eu          Belarusian	be      Bengali	bn      Bosnian	bs      Bulgarian	bg      Catalan	ca
        Cebuano	ceb         Chinese(Simplified)	zh-CN           Chinese (Traditional)	zh-TW
        Corsican	co      Croatian	hr      Czech	cs      Danish	da      Dutch	nl          English	en
        Esperanto	eo      Estonian	et      Finnish	fi      French	fr      Frisian	fy          Galician	gl
        Georgian	ka      German	de          Greek	el      Gujarati	gu  Haitian Creole	ht  Hausa	ha
        Hawaiian	haw     Hebrew	he          Hindi	hi      Hmong	hmn     Hungarian	hu      Icelandic	is
        Igbo	ig          Indonesian	id      Irish	ga      Italian	it      Japanese	ja      Javanese	jw
        ...

        Explore more google translate supported language please visit: https://cloud.google.com/translate/docs/languages
        :param text: Origin text
        :param src_lang: source language. the ISO-639-1 language code of the input text
        :param target_lang: target language. the ISO-639-1 language code of the output text
        :return: translated text
        """
        text_list = [text]
        translated = ''
        asyncio.run(self.async_translate_lines(text_list, src_lang=src_lang, target_lang=target_lang))

        for idx, item in enumerate(self.translated_list):
            if idx == len(self.translated_list)-1:
                translated += item.text
            else:
                translated += f"{item.text}\n"
        return translated

    async def async_translate_lines(self, text_list: list, src_lang: str, target_lang: str):
        
        async with googletrans.Translator() as translator:
            last_idx = 0
            total_length = 0
            for i in range(len(text_list)):
                total_length += len(text_list[i])
                if total_length > self.max_limited:
                    #translated += self.translate('\n'.join(text_list[last_idx:i]), src_lang, target_lang)
                    print(src_lang)
                    print(target_lang)
                    print(total_length)
                    self.translated_list.append(await translator.translate('\n'.join(text_list[last_idx:i]), src=src_lang, dest=target_lang))
                    await asyncio.sleep(1)
                    last_idx = i
                    total_length = 0
            self.translated_list.append(await translator.translate('\n'.join(text_list[last_idx:]), src=src_lang, dest=target_lang))
    

    def translate_lines(self, text_list: list, src_lang: str, target_lang: str) -> str:
        """
        Translate a text list into sentences.
        :param text_list:
        :param src_lang:
        :param target_lang:
        :return:
        """
        translated = ''
        asyncio.run(self.async_translate_lines(text_list, src_lang=src_lang, target_lang=target_lang))

        for idx, item in enumerate(self.translated_list):
            if idx == len(self.translated_list)-1:
                translated += item.text
            else:
                translated += f"{item.text}\n"
        return translated


if __name__ == '__main__':
    t = Translator()
    raw_text = "The Translation API's recognition engine supports a wide variety of languages for the Phrase-Based \
    Machine Translation (PBMT) and Neural Machine Translation (NMT) models. \nThese languages are specified within a \
    recognition request using language code parameters as noted on this page. \nMost language code parameters conform \
    to ISO-639-1 identifiers, except where noted."
    print(t.translate(raw_text, src_lang='en', target_lang='Zh-CN'))
    print(t.translate(raw_text, src_lang='en', target_lang='ja'))


