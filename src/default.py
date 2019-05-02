# -*- coding: utf-8 -*-

import os
import sys
import commons
import unicodedata
from xml.dom.minidom import parse, Document

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
	xbmcgui = sys.modules["__main__"].xbmcgui
else:
	import xbmcgui



class RssEditorDialog(xbmcgui.WindowXMLDialog):
	_TITLE = 5000
	_URLIST = 5110
	_ADDBTN = 5230
	_DELBTN = 5240
	_OKBTN  = 5210
	_CANCEL = 5220

	def __init__(self, *args, **kwargs):
		self.setNum = 'set1'
		self.parser = XMLParser()
		if self.parser.feedsTree:
			self.doModal()


	def onInit(self):
		self.setControls()
		self.feedsList = self.parser.feedsList[self.setNum]['feedslist']
		self.showDialog()


	def setControls(self):
		# controls used for data manipulation
		self.ListControl = self.getControl(self._URLIST)
		self.AddButtonControl = self.getControl(self._ADDBTN)
		self.RemoveButtonControl = self.getControl(self._DELBTN)
		self.OkButtonControl = self.getControl(self._OKBTN)
		self.CancelButtonControl = self.getControl(self._CANCEL)


	def showDialog(self):
		self.getControl(self._TITLE).setLabel(commons.translate(32000))
		self.updateFeedsList()


	def closeDialog(self):
		self.close()


	def onClick(self, controlId):
		# edit existing feed
		if controlId == self._URLIST:
			position = self.ListControl.getSelectedPosition()
			oldUrl = self.feedsList[position]['url']
			oldUpdateInterval = self.feedsList[position]['updateinterval']
			newUrl, newUpdateInterval = self.getNewFeed(oldUrl, oldUpdateInterval)
			if newUrl:
				self.feedsList[position] = {'url':newUrl, 'updateinterval':newUpdateInterval}
			self.updateFeedsList()
		#add new feed
		elif controlId == self._ADDBTN:
			newUrl, newUpdateInterval = self.getNewFeed()
			if newUrl:
				self.feedsList.append({'url':newUrl, 'updateinterval':newUpdateInterval})
			self.updateFeedsList()
		#remove existing feed
		elif controlId == self._DELBTN:
			self.removeFeed()
			self.updateFeedsList()
		#save xml
		elif controlId == self._OKBTN:
			self.parser.writeXmlToFile()
			self.closeDialog()
		#cancel dialog
		elif controlId == self._CANCEL:
			self.closeDialog()


	def onAction(self, action):
		if action in (9, 10):
			self.closeDialog()


	def removeFeed(self):
		position = self.ListControl.getSelectedPosition()
		self.feedsList.remove(self.feedsList[position])
		# add empty feed if last one is deleted
		if len(self.feedsList) < 1:
			self.feedsList = [{'url':'http://', 'updateinterval':'30'}]


	def getNewFeed(self, url='http://', newUpdateInterval='30'):
		kb = xbmc.Keyboard(url, commons.translate(32012), False)
		kb.doModal()
		if kb.isConfirmed():
			newUrl = kb.getText()
			newUpdateInterval = xbmcgui.Dialog().numeric(0, commons.translate(32013), newUpdateInterval)
		else:
			newUrl = None
		return newUrl, newUpdateInterval


	def updateFeedsList(self):
		self.ListControl.reset()
		for feed in self.feedsList:
			self.ListControl.addItem(feed['url'])



class XMLParser:

	def __init__(self):
		self.RssFeedsPath = xbmc.translatePath('special://userdata/RssFeeds.xml').decode("utf-8")
		sane = os.path.isfile(self.RssFeedsPath) and os.path.getsize(self.RssFeedsPath)
		if sane:
			try:
				self.feedsTree = parse(self.RssFeedsPath)
			except:
				commons.debug('Failed to parse %s, attempting to regenerate it..' %unicodedata.normalize('NFKD', self.RssFeedsPath).encode( 'ascii', 'ignore' ))
				self.regenerate()
				self.__init__()
			if self.feedsTree:
				self.feedsList = self.getCurrentRssFeeds()
		else:
			commons.debug('Could not open ' + unicodedata.normalize( 'NFKD', self.RssFeedsPath ).encode( 'ascii', 'ignore' ) + '. Either the file does not exist, or its size is zero.')
			self.regenerate()
			self.__init__()


	def regenerate(self):
		xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
		xml += '<rssfeeds>\n'
		xml += '<!-- RSS feeds. To have multiple feeds, just add a feed to the set. You can also have multiple sets. 	!-->\n'
		xml += '<!-- To use different sets in your skin, each must be called from skin with a unique id.			 	!-->\n'
		xml += '\t<set id="1">\n'
		xml += '\t\t<feed updateinterval="30">http://feeds.kodi.tv/xbmc</feed>\n'
		xml += '\t</set>\n'
		xml += '</rssfeeds>\n'
		f = open(self.RssFeedsPath, 'w')
		f.write(xml)
		f.close()


	def getCurrentRssFeeds(self):
		feedsList = dict()
		sets = self.feedsTree.getElementsByTagName('set')
		for s in sets:
			setName = 'set'+s.attributes["id"].value
			feedsList[setName] = {'feedslist':list(), 'attrs':dict()}
			# get attrs
			for attrib in s.attributes.keys():
				feedsList[setName]['attrs'][attrib] = s.attributes[attrib].value
			# get feedslist
			feeds = s.getElementsByTagName('feed')
			for feed in feeds:
				feedsList[setName]['feedslist'].append({'url':feed.firstChild.toxml(), 'updateinterval':feed.attributes['updateinterval'].value})
		return feedsList


	def writeXmlToFile(self):
		commons.debug('Writing to %s' % (unicodedata.normalize( 'NFKD', self.RssFeedsPath ).encode( 'ascii', 'ignore' )))
		# create the document
		doc = Document()
		# create root element
		rssfeedsTag = doc.createElement('rssfeeds')
		doc.appendChild(rssfeedsTag)
		# create comments
		c1Tag = doc.createComment('RSS feeds. To have multiple feeds, just add a feed to the set. You can also have multiple sets.')
		c2Tag = doc.createComment('To use different sets in your skin, each must be called from skin with a unique id.')
		rssfeedsTag.appendChild(c1Tag)
		rssfeedsTag.appendChild(c2Tag)
		for setNum in sorted(self.feedsList.keys()):
			# create sets
			setTag = doc.createElement('set')
			# create attributes
			setTag.setAttribute('id', self.feedsList[setNum]['attrs']['id'])
			# only write rtl tags if they've been explicitly set
			if 'rtl' in self.feedsList[setNum]['attrs']:
				setTag.setAttribute('rtl', self.feedsList[setNum]['attrs']['rtl'])
			rssfeedsTag.appendChild(setTag)
			# create feed elements
			for feed in self.feedsList[setNum]['feedslist']:
				feedTag = doc.createElement('feed')
				feedTag.setAttribute('updateinterval', feed['updateinterval'])
				feedUrl = doc.createTextNode(feed['url'])
				feedTag.appendChild(feedUrl)
				setTag.appendChild(feedTag)
		xml = doc.toprettyxml(indent = '  ', encoding = 'UTF-8')
		# hack for standalone attribute, minidom doesn't support DOM3
		xmlHeaderEnd = xml.find('?>')
		xml = xml[:xmlHeaderEnd]+' standalone="yes"'+xml[xmlHeaderEnd:]
		try:
			RssFeedsFile = open(self.RssFeedsPath, 'w')
			RssFeedsFile.write(xml)
			RssFeedsFile.close()
			self.refreshFeed()
		except IOError as error:
			commons.debug('Write failed: ', str(error))


	def refreshFeed(self):
		"""Refresh MCPi's rss feed so changes can be seen immediately"""
		xbmc.executebuiltin('refreshrss()')



if (__name__ == "__main__"):
	editor = RssEditorDialog("RSSEditorDialog.xml", commons.AddonPath())
	del editor

sys.modules.clear()
