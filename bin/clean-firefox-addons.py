#!/usr/bin/python
import os, sys, io
import json

def filter_addons(addons):
	fields_to_drop = [
			'description',
			'fullDescription',
			'screenshots',
			'icons',
			'averageRating',
			'contributionURL',
			'developers',
			'creator',
			'reviewCount',
			'supportURL',
			'reviewURL',
			'updateDate',
			'weeklyDownloads',
			]
	for addon in addons['addons']:
		for name in fields_to_drop:
			if name in addon:
				del addon[name]
	return addons

def filter_extensions(extensions):
	fields_to_drop = [
		'locales',
		'defaultLocale',
		'path',
		'seen',
		'rootURI',
		'recommendationState',
		'installTelemetryInfo',
		'icons',
		'applyBackgroundUpdates',
		'incognito',
		'installOrigins',
		'targetApplications',
		'targetPlatforms',
		'startupData',
		'optionalPermissions',
		'userPermissions',
		'installDate',
		'signedDate',
		'updateDate',
		'iconURL',
		'updateURL',
		'optionsURL',
		'releaseNotesURI',
		]
	filtered = []
	for extension in extensions['addons']:
		if extension.get('userDisabled'):
			continue
		if extension.get('id') == "addons-restricted-domains@mozilla.com": # Built-in addon for Brazil only.
			continue
		if extension.get('location') in ['app-builtin', 'app-system-defaults']:
			continue
		for name in fields_to_drop:
			if name in extension:
				del extension[name]
		filtered.append(extension)
	extensions['addons'] = sorted(filtered, key=lambda extension: extension.get('location', '') + extension.get('id'))
	return extensions

data = json.loads(sys.stdin.read())
if sys.argv[1:] == ['addons']:
	data = filter_addons(data)
elif sys.argv[1:] == ['extensions']:
	data = filter_extensions(data)
else:
	raise RuntimeError('Usage: {0} [addons|extensions]'.format(__file__))
print(json.dumps(data, indent='\t', sort_keys=True))
