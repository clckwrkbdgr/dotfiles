#!/bin/bash
IN_JID=${1:-NONE}

shopt -s dotglob

TIME_COLOR="#888"
IN_COLOR="#f00"
OUT_COLOR="#00f"
IN_NAME="$IN_JID"
OUT_NAME="You"

QUERY=" SELECT \
    strftime('<font color=\"$TIME_COLOR\">[%d/%m/%Y %H:%M:%S] </font>', l.time, 'unixepoch') \
    || \
    CASE l.kind \
        WHEN 0 THEN 'status message: ' \
        WHEN 4 THEN '<font color=\"$IN_COLOR\">$IN_NAME</font>: ' \
        WHEN 6 THEN '<font color=\"$OUT_COLOR\">$OUT_NAME</font>: ' \
        ELSE 'UNKNOWN' \
    END \
    || \
    l.message \
FROM (SELECT * FROM logs ORDER BY time) AS l \
WHERE \
    l.jid_id IN (SELECT jid_id FROM jids where jid like '%$IN_JID%') \
    AND l.kind <> 7 \
    AND (l.show IS NULL OR l.show <> 5) \
	AND strftime('%Y-%m', l.time, 'unixepoch')= "
MONTH_QUERY="SELECT DISTINCT strftime('%Y-%m', l.time, 'unixepoch') FROM logs l \
WHERE l.jid_id IN (SELECT jid_id FROM jids where jid like '%$IN_JID%') ORDER BY 1; "

HTML_HEAD="<html> \
    <meta http-equiv=content-type content=\"text/html; charset=utf-8\" /> \
    <style type=\"text/css\">
        pre {
            white-space: pre-wrap;       /* css-3 */
            white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
            white-space: -pre-wrap;      /* Opera 4-6 */
            white-space: -o-pre-wrap;    /* Opera 7 */
            word-wrap: break-word;       /* Internet Explorer 5.5+ */
        }
    </style>
    <body>
    <pre> \
"
HTML_TAIL=""

echo "$MONTH_QUERY" | sqlite3 ~/.local/share/gajim/logs.db | while read month; do
	echo $month
	(echo "$HTML_HEAD";
	echo "${QUERY}'${month}';" | sqlite3 ~/.local/share/gajim/logs.db;
	echo "$HTML_TAIL";
	) >"${IN_JID}-${month}.html"
done

shopt -u dotglob
