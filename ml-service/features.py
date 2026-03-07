"""
Module to extract relevant features from:
- HTML
- URL
- TEXT
"""

import re
from urllib.parse import urlparse
from math import log
from string import punctuation
import email
from email.utils import parseaddr
from pyquery import PyQuery
from datetime import datetime

"""
Module to extract relevant features from Email HTML.
Tailored specifically for phishing detection in email sandboxes.
"""

import re
from math import log
from string import punctuation
from pyquery import PyQuery

class HTMLFeatures:
    """Extracts features specifically targeted at Email HTML anomalies."""

    def __init__(self, html: str):
        self.html = html.lower()
        self.pq = PyQuery(html)
        # JavaScript is almost never legitimate in an email
        self.suspicious_functions = ['eval', 'unescape', 'document.write', 'innerhtml', 'window.open', 'settimeout']

    def __get_entropy(self, text):
        if not text:
            return 0
        probs = [text.count(c) / len(text) for c in set(text)]
        return round(-sum([p * log(p) / log(2.0) for p in probs]), 3)

    # ---------------------------------------------------------
    # 1. TEXT & CONTENT METRICS (To detect AI-generated or spun spam)
    # ---------------------------------------------------------
    def page_entropy(self):
        return self.__get_entropy(self.pq.text())

    def html_length(self):
        return len(self.html)

    def text_length(self):
        return len(self.pq.text())

    def text_to_html_ratio(self):
        """Spammers often use massive HTML with very little visible text."""
        html_len = self.html_length()
        return round(self.text_length() / html_len, 3) if html_len > 0 else 0

    def number_of_words(self):
        return len(self.pq.text().split())

    # ---------------------------------------------------------
    # 2. EMAIL SANDBOX VIOLATIONS (The "Smoking Guns")
    # ---------------------------------------------------------
    def number_of_script_tags(self):
        """Any script tag in an email is a critical red flag."""
        return len(self.pq('script'))

    def number_of_forms(self):
        """Legitimate emails link to websites; they don't embed forms."""
        return len(self.pq('form'))

    def number_of_input_fields(self):
        """Counts text boxes, checkboxes, etc., embedded in the email."""
        return len(self.pq('input')) + len(self.pq('select')) + len(self.pq('textarea'))

    def number_of_password_fields(self):
        """Extremely malicious if found inside an email."""
        return len(self.pq('input[type="password"]'))

    def number_of_iframes(self):
        """Often used for tracking pixels or downloading malicious payloads."""
        return len(self.pq('iframe')) + len(self.pq('frame'))

    def number_of_objects_or_embeds(self):
        """Flash, Java applets, or external plugins (highly suspicious)."""
        return len(self.pq('object')) + len(self.pq('embed'))

    def has_meta_refresh(self):
        """Checks if the email tries to automatically redirect the user's browser."""
        meta_tags = self.pq('meta')
        for tag in meta_tags.items():
            if tag.attr('http-equiv') and tag.attr('http-equiv').lower() == 'refresh':
                return 1
        return 0

    # ---------------------------------------------------------
    # 3. SPAM FILTER EVASION TACTICS
    # ---------------------------------------------------------
    def number_of_hidden_tags(self):
        """Tags hidden via CSS to stuff 'good' words to fool basic spam filters."""
        hidden_class = self.pq('.hidden') + self.pq('#hidden')
        hidden_attr = self.pq('*[visibility="hidden"]') + self.pq('*[display="none"]')
        return len(hidden_class) + len(hidden_attr)

    def zero_font_size_text_count(self):
        """Detects text shrunk to 0px so the user can't see it, but filters read it."""
        return len(re.findall(r'font-size:\s*0\s*(?:px|em|pt|rem)?', self.html))

    def hex_encoded_characters_num(self):
        """Spammers hex-encode HTML (e.g., %3C instead of <) to bypass signature checks."""
        return len(re.findall(r'%[0-9a-fA-F]{2}', self.html))

    def base64_images_num(self):
        """Phishers embed Base64 images directly to bypass remote-image blocking."""
        return len(re.findall(r'data:image/[a-zA-Z]+;base64,', self.html))

    # ---------------------------------------------------------
    # 4. LINK & IMAGE ANOMALIES
    # ---------------------------------------------------------
    def total_hyperlinks(self):
        return len(self.pq('a'))

    def images_to_links_ratio(self):
        """If an email is just one massive image wrapped in a single link."""
        imgs = len(self.pq('img'))
        links = self.total_hyperlinks()
        return round(imgs / links, 3) if links > 0 else imgs

    def empty_links_num(self):
        """Links that go nowhere (href="#"), often used in copy-pasted templates."""
        return len(self.pq('a[href="#"]')) + len(self.pq('a:not([href])'))

    def link_text_mismatch_count(self):
        """Detects when the visible text says 'paypal.com' but the href goes elsewhere."""
        count = 0
        for a in self.pq('a').items():
            href = a.attr('href')
            text = a.text().strip()
            # If the visible text looks like a domain, but isn't found in the actual link destination
            if href and text and '.' in text and text.lower() not in href.lower():
                count += 1
        return count

    # ---------------------------------------------------------
    # 5. JAVASCRIPT & DOM ANOMALIES (If scripts are present)
    # ---------------------------------------------------------
    def number_of_suspicious_functions(self):
        script_content = self.pq('script').text().lower()
        return sum(1 for i in self.suspicious_functions if i in script_content)

    def number_of_dom_modifying_functions(self):
        regex_dom = [
            r'createelement\s*\(', r'appendchild\s*\(', r'document\.write\s*\(',
            r'setattribute\s*\('
        ]
        script_content = self.pq('script').text().lower()
        return sum(len(re.findall(regex, script_content)) for regex in regex_dom)

    def get_features(self):
        """Compiles all email-specific HTML features into a dictionary for XGBoost."""
        return {
            # Content Metrics
            'html_page_entropy': self.page_entropy(),
            'html_length': self.html_length(),
            'html_text_length': self.text_length(),
            'html_text_to_html_ratio': self.text_to_html_ratio(),
            'html_words_num': self.number_of_words(),
            
            # Email Sandbox Violations
            'html_script_tags_num': self.number_of_script_tags(),
            'html_forms_num': self.number_of_forms(),
            'html_inputs_num': self.number_of_input_fields(),
            'html_password_fields_num': self.number_of_password_fields(),
            'html_iframes_num': self.number_of_iframes(),
            'html_objects_embeds_num': self.number_of_objects_or_embeds(),
            'html_has_meta_refresh': self.has_meta_refresh(),
            
            # Evasion Tactics
            'html_hidden_tags_num': self.number_of_hidden_tags(),
            'html_zero_font_text_num': self.zero_font_size_text_count(),
            'html_hex_encoded_chars': self.hex_encoded_characters_num(),
            'html_base64_images_num': self.base64_images_num(),
            
            # Links & Images
            'html_total_links': self.total_hyperlinks(),
            'html_images_to_links_ratio': self.images_to_links_ratio(),
            'html_empty_links_num': self.empty_links_num(),
            'html_link_text_mismatch_num': self.link_text_mismatch_count(),
            
            # Malicious Actions
            'html_suspicious_func_num': self.number_of_suspicious_functions(),
            'html_dom_mod_func_num': self.number_of_dom_modifying_functions()
        }

###########################
###### URL FEATURES #######
###########################

class URLFeatures:
    """Extracts URL features"""

    def __init__(self, url: str):
        self.url = url
        self.urlparsed = urlparse(url)
        self.shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                      r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                      r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                      r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                      r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                      r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                      r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                      r"tr\.im|link\.zip\.net"

    def entropy(self):
        """Calculates URL entropy"""
        text = self.url.lower()
        probs = [text.count(c) / len(text) for c in set(text)]
        return round(-sum([p * log(p) / log(2.0) for p in probs]), 3)

    def length(self):
        """url length"""
        return len(self.url)

    def path_length(self):
        """url path length"""
        return len(self.urlparsed.path)

    def host_length(self):
        """url host length"""
        return len(self.urlparsed.netloc)

    def host_is_ip(self):
        """url host has ip form?"""
        host = self.urlparsed.netloc
        pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        match = pattern.match(host)
        return match is not None

    def has_port(self):
        """url has a port inside?"""
        has_port = self.urlparsed.netloc.split(':')
        return len(has_port) > 1 and has_port[-1].isdigit()

    def number_of_digits(self):
        """number of digits in the url"""
        digits = [i for i in self.url if i.isdigit()]
        return len(digits)

    def number_of_parameters(self):
        """number of parameters in the url"""
        params = self.urlparsed.query
        return 0 if params == '' else len(params.split('&'))

    def is_encoded(self):
        """is the url encoded?"""
        return '%' in self.url.lower()

    def num_encoded_char(self):
        """number of encoded characters in the url"""
        encs = [i for i in self.url if i == '%']
        return len(encs)

    def number_of_subdirectories(self):
        """number of subdirectories in the url"""
        d = self.urlparsed.path.split('/')
        return len(d)

    def number_of_periods(self):
        """number of periods in the url"""
        periods = [i for i in self.url if i == '.']
        return len(periods)

    def prefix_suffix_presence(self):
        """Checking the presence of '-' in the domain part of URL"""
        return True if '-' in self.urlparsed.netloc else False

    def use_shortening_services(self):
        """Check if URL is using a shortening service"""
        return True if re.search(self.shortening_services, self.url) else False

    def has_double_slash_in_wrong_position(self):
        """Checks the presence of '//' in the URL"""
        pos = self.url.rfind('//')
        return True if pos > 7 else False

    def has_haveat_sign(self):
        """Checks for the presence of '@' symbol in the URL"""
        return True if '@' in self.url else False

    def has_client_in_string(self):
        """url has the keyword 'client' in the url?"""
        return 'client' in self.url.lower()

    def has_admin_in_string(self):
        """url has the keyword 'admin' in the url?"""
        return 'admin' in self.url.lower()

    def has_server_in_string(self):
        """url has the keyword 'server' in the url?"""
        return 'server' in self.url.lower()

    def has_login_in_string(self):
        """url has the keyword 'login' in the url?"""
        return 'login' in self.url.lower()

    def get_features(self):
        """Extracts automatically the URL features"""
        return {
            'use_shortening_service': self.use_shortening_services(),
            'prefix_suffix_presence': self.prefix_suffix_presence(),
            'has_double_slash': self.has_double_slash_in_wrong_position(),
            'has_haveat_sign': self.has_haveat_sign(),
            'has_port': self.has_port(),
            'has_admin_keyword': self.has_admin_in_string(),
            'has_server_keyword': self.has_server_in_string(),
            'has_login_keyword': self.has_login_in_string(),
            'has_client_keyword': self.has_client_in_string(),
            'host_is_ip': self.host_is_ip(),
            'is_encoded': self.is_encoded(),
            'length': self.length(),
            'path_length': self.path_length(),
            'host_length': self.host_length(),
            'entropy': self.entropy(),
            'digits_num': self.number_of_digits(),
            'subdirectories_num': self.number_of_subdirectories(),
            'periods_num': self.number_of_periods(),
            'params_num': self.number_of_parameters()
        }

###########################
###### TEXT FEATURES ######
###########################

class TextFeatures:
    """Extracts Text Features"""

    def __init__(self, text : str) -> None:
        self.text = text

    def length(self):
        """Return text length"""
        return len(self.text)

    def entropy(self):
        """Calculates text entropy"""
        text = self.text.lower()
        probs = [text.count(c) / len(text) for c in set(text)]
        return round(-sum([p * log(p) / log(2.0) for p in probs]), 3)

    def words_number(self):
        """Returns number of words in the text"""
        return len(self.text.split(' '))

    def digits_number(self):
        """Returns number of digit characters in the text"""
        return sum(c.isdigit() for c in self.text)

    def has_email_adress(self):
        """Check if email address is present in the text"""
        mail_regex = r"(?:[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
        return True if re.search(mail_regex, self.text) else False

    def has_url(self):
        """Check if a URL is present in the text"""
        url_regex = r"(?i)\b((?:https?:(?:\/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b\/?(?!@)))"
        return True if re.search(url_regex, self.text) else False

    def get_features(self):
        """Get dictionary with features and their values"""
        return {
            'has_email': self.has_email_adress(),
            'has_url': self.has_url(),
            'length': self.length(),
            'entropy': self.entropy(),
            'words_num': self.words_number(),
            'digits_num': self.digits_number(),
        }


class TeddFeatureExtractor:
    def __init__(self):
        # The exact order of columns from your dataset
        self.feature_names = [
            'hops', 'missing_received1', 'missing_received2', 'missing_received3', 'missing_received4', 'missing_received5', 'missing_received6', 'missing_received7', 'missing_received8', 'missing_received9', 'missing_received10', 'missing_received11', 'missing_received12', 'missing_received13', 'missing_received14', 'missing_received15', 'missing_received16',
            'missing_subject', 'missing_date', 'missing_message-id', 'missing_from', 'missing_return-path', 'missing_to', 'missing_content-type', 'missing_mime-version', 'missing_x-mailer', 'missing_content-transfer-encoding', 'missing_x-mimeole', 'missing_x-priority', 'missing_list-id', 'missing_lines', 'missing_x-virus-scanned', 'missing_status', 'missing_content-length', 'missing_precedence', 'missing_delivered-to', 'missing_list-unsubscribe', 'missing_list-subscribe', 'missing_list-post', 'missing_list-help', 'missing_x-msmail-priority', 'missing_x-spam-status', 'missing_sender', 'missing_errors-to', 'missing_x-beenthere', 'missing_list-archive', 'missing_reply-to', 'missing_x-mailman-version', 'missing_x-miltered', 'missing_x-uuid', 'missing_x-virus-status', 'missing_x-spam-level', 'missing_x-spam-checker-version', 'missing_references', 'missing_in-reply-to', 'missing_user-agent', 'missing_thread-index', 'missing_cc', 'missing_received-spf', 'missing_x-original-to', 'missing_content-disposition', 'missing_mailing-list', 'missing_x-spam-check-by', 'missing_domainkey-signature', 'missing_importance', 'missing_x-mailing-list',
            'content-encoding-val', 'received_str_forged', 'str_content-encoding_empty', 'str_from_question', 'str_from_exclam', 'str_from_chevron', 'str_to_chevron', 'str_to_undisclosed', 'str_to_empty', 'str_message-ID_dollar', 'str_return-path_bounce', 'str_return-path_empty', 'str_reply-to_question', 'str_received-SPF_bad', 'str_received-SPF_softfail', 'str_received-SPF_fail', 'str_content-type_texthtml', 'str_precedence_list',
            'length_from', 'num_recipients_to', 'num_recipients_cc', 'num_recipients_from', 'number_replies', 'time_zone', 'x-priority', 'content-length', 'lines', 'day_of_week', 'date_comp_date_received', 'span_time',
            'conseq_num_received_is_one', 'conseq_received_good', 'conseq_received_bad', 'conseq_received_unknown', 'conseq_received_date', 'email_match_from_reply-to', 'domain_val_message-id',
            'domain_match_message-id_from', 'domain_match_from_return-path', 'domain_match_message-id_return-path', 'domain_match_message-id_sender', 'domain_match_message-id_reply-to', 'domain_match_return-path_reply-to', 'domain_match_reply-to_to', 'domain_match_to_in-reply-to', 'domain_match_errors-to_message-id', 'domain_match_errors-to_from', 'domain_match_errors-to_sender', 'domain_match_errors-to_reply-to', 'domain_match_sender_from', 'domain_match_references_reply-to', 'domain_match_references_in-reply-to', 'domain_match_references_to', 'domain_match_from_reply-to', 'domain_match_to_from', 'domain_match_to_message-id', 'domain_match_reply-to_received', 'domain_match_to_received', 'domain_match_return-path_received', 'domain_match_from_received'
        ]

    def _get_domains(self, header_str):
        if not header_str: return []
        emails = re.findall(r'([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', header_str)
        domains = []
        for e in emails:
            parts = e.split('@')[-1].split('.')
            if len(parts) >= 2:
                main_domain = parts[-2] + '.' + re.sub(r'\W+', '', parts[-1])
                domains.append(main_domain.lower())
        return domains

    def _domain_match(self, d1_list, d2_list):
        if not d1_list or not d2_list: return 0
        return 1 if any(d1 == d2 for d1 in d1_list for d2 in d2_list) else 0

    def extract(self, raw_email_text):
        msg = email.message_from_string(raw_email_text)
        features = {col: 0.0 for col in self.feature_names} # Initialize all to 0.0

        # --- 1. Header Extraction ---
        headers = {k.lower(): str(v).replace('\n', ' ').replace('\t', ' ') for k, v in msg.items()}
        received_list = msg.get_all('Received') or []

        # --- 2. Missing Features Check ---
        for f in self.feature_names:
            # FIX: Ensure we only parse numbered received features
            if f.startswith('missing_received') and f.replace('missing_received', '').isdigit():
                num = int(f.replace('missing_received', ''))
                features[f] = 0.0 if len(received_list) >= num else 1.0
            elif f.startswith('missing_'):
                header_name = f.replace('missing_', '')
                features[f] = 0.0 if msg.get(header_name) else 1.0

        # --- 3. Base Counts & Lengths ---
        raw_hops = len(received_list)
        features['hops'] = 0 if raw_hops <= 2 else (1 if raw_hops <= 5 else 2)

        from_val = headers.get('from', '')
        features['length_from'] = 0 if len(from_val) > 40 else 1

        for field in ['to', 'cc', 'from']:
            num_rec = len(re.findall(r'([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', headers.get(field, '')))
            features[f'num_recipients_{field}'] = 0 if num_rec == 0 else (1 if num_rec == 1 else 2)

        ref_count = len(re.findall(r'<.*?>', headers.get('references', '')))
        features['number_replies'] = 0 if ref_count >= 1 else 1

        # --- 4. String Match Features ---
        cte = headers.get('content-transfer-encoding', '')
        features['content-encoding-val'] = 1 if not re.search(r'(?i)8bit|7bit', cte) else 0
        features['str_content-encoding_empty'] = 1.0 if cte == "" else 0.0

        features['received_str_forged'] = 1 if any('forged' in r.lower() for r in received_list) else 0
        features['str_from_question'] = 1.0 if '?' in from_val else 0.0
        features['str_from_exclam'] = 1.0 if '!' in from_val else 0.0
        features['str_from_chevron'] = 1.0 if re.search(r'<.+>', from_val) else 0.0
        features['str_to_chevron'] = 1.0 if re.search(r'<.+>', headers.get('to', '')) else 0.0
        features['str_to_undisclosed'] = 1.0 if 'Undisclosed Recipients' in headers.get('to', '') else 0.0
        features['str_to_empty'] = 1.0 if headers.get('to', '') == "" else 0.0
        features['str_message-ID_dollar'] = 1.0 if '$' in headers.get('message-id', '') else 0.0
        features['str_return-path_bounce'] = 1.0 if 'bounce' in headers.get('return-path', '').lower() else 0.0
        features['str_reply-to_question'] = 1.0 if '?' in headers.get('reply-to', '') else 0.0

        spf = headers.get('received-spf', '').lower()
        features['str_received-SPF_bad'] = 1.0 if 'bad' in spf else 0.0
        features['str_received-SPF_softfail'] = 1.0 if 'softfail' in spf else 0.0
        features['str_received-SPF_fail'] = 1.0 if 'fail' in spf else 0.0
        features['str_content-type_texthtml'] = 1.0 if 'text/html' in headers.get('content-type', '').lower() else 0.0
        features['str_precedence_list'] = 1.0 if 'list' in headers.get('precedence', '').lower() else 0.0

        # --- 5. Discretized Numeric Headers ---
        priority_val = re.search(r'(\d+)', headers.get('x-priority', '0'))
        p_num = int(priority_val.group(1)) if priority_val else 0
        features['x-priority'] = 0 if p_num != 3 else 1

        cl_val = re.search(r'(\d+)', headers.get('content-length', '0'))
        cl_num = int(cl_val.group(1)) if cl_val else 0
        features['content-length'] = 0 if cl_num < 1 else (1 if cl_num < 1274 else (2 if cl_num < 2348 else (3 if cl_num < 5798 else 4)))

        lines_val = re.search(r'(\d+)', headers.get('lines', '0'))
        l_num = int(lines_val.group(1)) if lines_val else 0
        features['lines'] = 0 if l_num == 0 else (1 if l_num <= 30 else (2 if l_num <= 54 else (3 if l_num <= 119 else 4)))

        # --- 6. Date & Time ---
        tz = email.utils.parsedate_tz(headers.get('date', ''))
        features['time_zone'] = 0
        day_str = 'NA'
        if tz:
            tz_hours = int(tz[9] / 3600) % 24 if tz[9] else 0
            features['time_zone'] = 1 if tz_hours == 20 else 0
            try:
                day_str = datetime.fromtimestamp(email.utils.mktime_tz(tz)).strftime("%A")
            except: pass

        days = ['NA', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        features['day_of_week'] = days.index(day_str) if day_str in days else 0

        first_rec = received_list[-1].split(';')[-1] if received_list else ""
        last_rec = received_list[0].split(';')[-1] if received_list else ""
        d_first = email.utils.parsedate_tz(first_rec)
        d_last = email.utils.parsedate_tz(last_rec)

        if tz and d_last:
            try: diff = email.utils.mktime_tz(d_last) - email.utils.mktime_tz(tz)
            except: diff = -1
            features['date_comp_date_received'] = 0 if diff < 0 else 1

        if d_first and d_last:
            try: span = email.utils.mktime_tz(d_last) - email.utils.mktime_tz(d_first)
            except: span = -1
            features['span_time'] = 0 if span < 0 else (1 if span < 10 else (2 if span < 47 else (3 if span < 1100 else 4)))

        # --- 7. Domain Matching ---
        doms = {
            'message-id': self._get_domains(headers.get('message-id', '')),
            'from': self._get_domains(headers.get('from', '')),
            'return-path': self._get_domains(headers.get('return-path', '')),
            'sender': self._get_domains(headers.get('sender', '')),
            'reply-to': self._get_domains(headers.get('reply-to', '')),
            'to': self._get_domains(headers.get('to', '')),
            'in-reply-to': self._get_domains(headers.get('in-reply-to', '')),
            'errors-to': self._get_domains(headers.get('errors-to', '')),
            'references': self._get_domains(headers.get('references', ''))
        }

        features['domain_val_message-id'] = 1 if any('uwaterloo.ca' in d for d in doms['message-id']) else 0

        matches_to_check = [
            ('message-id', 'from'), ('from', 'return-path'), ('message-id', 'return-path'),
            ('message-id', 'sender'), ('message-id', 'reply-to'), ('return-path', 'reply-to'),
            ('reply-to', 'to'), ('to', 'in-reply-to'), ('errors-to', 'message-id'),
            ('errors-to', 'from'), ('errors-to', 'sender'), ('errors-to', 'reply-to'),
            ('sender', 'from'), ('references', 'reply-to'), ('references', 'in-reply-to'),
            ('references', 'to'), ('from', 'reply-to'), ('to', 'from'), ('to', 'message-id')
        ]

        for f1, f2 in matches_to_check:
            features[f'domain_match_{f1}_{f2}'] = self._domain_match(doms[f1], doms[f2])

        # Email match check
        features['email_match_from_reply-to'] = 1 if any(e1 == e2 for e1 in re.findall(r'([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', headers.get('from', '')) for e2 in re.findall(r'([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', headers.get('reply-to', ''))) else 0

        # Conseq logic fallback (Uses regex for speed over full parser in single-instance)
        features['conseq_num_received_is_one'] = 1 if raw_hops == 1 else 0
        features['conseq_received_good'] = 1 if raw_hops > 1 else 0

