import urllib2

class SaltyBot:
    def __init__(self):
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36')]
        self.opener.addheaders.append(('Cookie', 'PHPSESSID=4ik496l8404976f0m98q63go84'))
        self.opener.addheaders.append(('Cookie', '__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623'))
        self.opener.addheaders.append(('Cookie', '_ga=GA1.2.81538886.1432266024'))
