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


class HeaderFeatures:
    """Extracts Email Header Features for phishing detection"""

    def __init__(self, header_dict: dict):
        """
        header_dict should contain comprehensive header information including authentication headers
        """
        self.from_addr = header_dict.get('from', '')
        self.to_addr = header_dict.get('to', '')
        self.subject = header_dict.get('subject', '')
        self.date = header_dict.get('date', '')
        self.cc = header_dict.get('cc', '')
        self.bcc = header_dict.get('bcc', '')
        self.reply_to = header_dict.get('reply_to', '')
        # Authentication headers
        self.delivered_to = header_dict.get('delivered_to', '')
        self.return_path = header_dict.get('return_path', '')
        self.message_id = header_dict.get('message_id', '')
        self.x_originating_ip = header_dict.get('x_originating_ip', '')
        self.x_mailer = header_dict.get('x_mailer', '')
        # Authentication results
        self.dkim_signature = header_dict.get('dkim_result', '')
        self.authentication_results = header_dict.get('authentication_results', '')
        self.received_spf = header_dict.get('received_spf', '')
        # Multiple received headers
        self.received_headers = header_dict.get('received_headers', []) or []
        # Arc headers
        self.arc_seal = header_dict.get('arc_seal', '')
        self.arc_message_signature = header_dict.get('arc_message_signature', '')
        self.arc_authentication_results = header_dict.get('arc_authentication_results', '')
        # Forwarding headers
        self.x_forwarded_for = header_dict.get('x_forwarded_for', '')
        self.x_forwarded_encrypted = header_dict.get('x_forwarded_encrypted', '')

    # ===== BASIC HEADER CHECKS =====
    def has_from_address(self):
        """Check if From address exists"""
        return bool(self.from_addr)

    def has_to_address(self):
        """Check if To address exists"""
        return bool(self.to_addr)

    def from_to_mismatch(self):
        """Check if From and To addresses are the same (suspicious)"""
        if self.from_addr and self.to_addr:
            from_domain = self.from_addr.split('@')[-1] if '@' in self.from_addr else ''
            to_domain = self.to_addr.split('@')[-1] if '@' in self.to_addr else ''
            return from_domain == to_domain
        return False

    def reply_to_mismatch(self):
        """Check if Reply-To differs from From address (suspicious)"""
        if self.reply_to and self.from_addr:
            return self.reply_to.lower() != self.from_addr.lower()
        return False

    def from_contains_suspicious_keywords(self):
        """Check for suspicious keywords in From address"""
        suspicious = ['support', 'noreply', 'mail', 'notification', 'alert', 'verify', 'confirm', 'urgent', 'action']
        from_lower = self.from_addr.lower()
        return any(keyword in from_lower for keyword in suspicious)

    def subject_urgency_indicators(self):
        """Check for urgency indicators in subject"""
        urgent_keywords = ['urgent', 'immediate', 'verify', 'confirm', 'action required', 'urgent action', 'act now', 'limited time']
        subject_lower = self.subject.lower()
        return sum(1 for keyword in urgent_keywords if keyword in subject_lower)

    def subject_suspicious_keywords(self):
        """Check for phishing-related keywords in subject"""
        phishing_keywords = ['confirm', 'verify', 'update', 'suspended', 'locked', 'click', 'click here', 'act', 'reset', 'validate']
        subject_lower = self.subject.lower()
        return sum(1 for keyword in phishing_keywords if keyword in subject_lower)

    def cc_bcc_empty(self):
        """Check if CC and BCC are empty (more likely to be phishing)"""
        return not self.cc and not self.bcc

    def to_multiple_recipients(self):
        """Check if email is sent to multiple recipients"""
        return ',' in self.to_addr if self.to_addr else False

    def subject_length(self):
        """Get subject length"""
        return len(self.subject)

    def subject_entropy(self):
        """Calculate subject entropy"""
        if not self.subject:
            return 0
        subject_lower = self.subject.lower()
        probs = [subject_lower.count(c) / len(subject_lower) for c in set(subject_lower)]
        return round(-sum([p * log(p) / log(2.0) for p in probs]), 3) if probs else 0

    def from_is_ip_address(self):
        """Check if From address uses IP instead of domain"""
        try:
            if '@' in self.from_addr:
                domain = self.from_addr.split('@')[1]
                parts = domain.split('.')
                return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
        except:
            pass
        return False

    def has_display_name_mismatch(self):
        """Check if display name doesn't match actual email domain"""
        if '<' in self.from_addr and '>' in self.from_addr:
            display_part = self.from_addr[:self.from_addr.index('<')]
            email_part = self.from_addr[self.from_addr.index('<')+1:self.from_addr.index('>')]
            # Check if display name contains suspicious company names
            suspicious_companies = ['paypal', 'amazon', 'apple', 'microsoft', 'google', 'bank', 'wells fargo', 'chase']
            display_lower = display_part.lower()
            email_domain = email_part.split('@')[-1] if '@' in email_part else ''
            for company in suspicious_companies:
                if company in display_lower and company not in email_domain:
                    return True
        return False

    # ===== AUTHENTICATION HEADER CHECKS =====
    def return_path_mismatch(self):
        """Check if Return-Path differs from From address"""
        if self.return_path and self.from_addr:
            return_domain = self.return_path.split('@')[-1].rstrip('>') if '@' in self.return_path else ''
            from_domain = self.from_addr.split('@')[-1] if '@' in self.from_addr else ''
            return return_domain != from_domain
        return False

    def delivered_to_mismatch(self):
        """Check if Delivered-To differs from To address"""
        if self.delivered_to and self.to_addr:
            return self.delivered_to.lower() != self.to_addr.lower()
        return False

    def dkim_pass(self):
        """Check if DKIM signature is present and passes"""
        if not self.dkim_signature:
            return 0
        dkim_lower = self.dkim_signature.lower()
        # Check for DKIM signature existence
        if 'dkim-signature' in dkim_lower or 'v=1' in dkim_lower:
            return 1
        return 0

    def spf_pass(self):
        """Check if SPF verification passed"""
        if not self.received_spf and not self.authentication_results:
            return 0
        
        combined = (self.received_spf + " " + self.authentication_results).lower()
        if 'spf=pass' in combined or 'pass' in combined.split('spf=')[0] if 'spf=' in combined else False:
            return 1
        if 'spf=fail' in combined or 'fail' in combined:
            return -1
        return 0

    def dmarc_pass(self):
        """Check if DMARC verification passed"""
        auth_results = self.authentication_results.lower()
        arc_results = self.arc_authentication_results.lower() if self.arc_authentication_results else ""
        
        combined = auth_results + " " + arc_results
        if 'dmarc=pass' in combined:
            return 1
        if 'dmarc=fail' in combined:
            return -1
        return 0

    def multiple_received_headers(self):
        """Count multiple Received headers (forwarding indicator)"""
        return len(self.received_headers) if self.received_headers else 0

    def suspicious_received_chain(self):
        """Check for suspicious routing in Received headers"""
        if not self.received_headers or len(self.received_headers) < 1:
            return 0
        
        # Look for suspicious patterns in received headers
        suspicious_count = 0
        for header in self.received_headers:
            header_lower = header.lower() if isinstance(header, str) else ""
            # Check for unusual routing or spoofed IPs
            if 'unknown' in header_lower or '[127.0.0.1]' in header_lower or '[0.0.0.0]' in header_lower:
                suspicious_count += 1
        
        return suspicious_count

    def has_x_originating_ip(self):
        """Check if X-Originating-IP header exists (Gmail/Office)"""
        return 1 if self.x_originating_ip else 0

    def has_arc_headers(self):
        """Check if ARC headers are present (authenticated routing)"""
        arc_count = 0
        if self.arc_seal:
            arc_count += 1
        if self.arc_message_signature:
            arc_count += 1
        if self.arc_authentication_results:
            arc_count += 1
        return arc_count

    def forwarding_indicators(self):
        """Check for forwarding headers (X-Forwarded-For, X-Forwarded-Encrypted)"""
        count = 0
        if self.x_forwarded_for:
            count += 1
        if self.x_forwarded_encrypted:
            count += 1
        return count

    def missing_message_id(self):
        """Check if Message-ID is missing (red flag)"""
        return 0 if self.message_id else 1

    def has_suspicious_mailer(self):
        """Check for suspicious X-Mailer values"""
        if not self.x_mailer:
            return 0
        
        suspicious_mailers = ['php', 'perl', 'python', 'java', 'vbscript', 'unknown']
        x_mailer_lower = self.x_mailer.lower()
        
        return 1 if any(mailer in x_mailer_lower for mailer in suspicious_mailers) else 0

    def get_features(self):
        """Get dictionary with all header features"""
        return {
            # Basic header checks
            'has_from_address': self.has_from_address(),
            'has_to_address': self.has_to_address(),
            'from_to_mismatch': self.from_to_mismatch(),
            'reply_to_mismatch': self.reply_to_mismatch(),
            'from_contains_suspicious': self.from_contains_suspicious_keywords(),
            'subject_urgency_count': self.subject_urgency_indicators(),
            'subject_phishing_keywords': self.subject_suspicious_keywords(),
            'cc_bcc_empty': self.cc_bcc_empty(),
            'to_multiple_recipients': self.to_multiple_recipients(),
            'subject_length': self.subject_length(),
            'subject_entropy': self.subject_entropy(),
            'from_is_ip': self.from_is_ip_address(),
            'display_name_mismatch': self.has_display_name_mismatch(),
            # Authentication header checks
            'return_path_mismatch': self.return_path_mismatch(),
            'delivered_to_mismatch': self.delivered_to_mismatch(),
            'dkim_signature_present': self.dkim_pass(),
            'spf_verification': self.spf_pass(),
            'dmarc_verification': self.dmarc_pass(),
            'multiple_received_headers': self.multiple_received_headers(),
            'suspicious_received_chain': self.suspicious_received_chain(),
            'has_x_originating_ip': self.has_x_originating_ip(),
            'arc_headers_count': self.has_arc_headers(),
            'forwarding_indicators': self.forwarding_indicators(),
            'missing_message_id': self.missing_message_id(),
            'suspicious_mailer': self.has_suspicious_mailer(),
        }

