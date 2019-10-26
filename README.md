
# plugin.audio.m3sr2019

MP3 Streams Reloaded

### Notes
  * Force fixed viewmode in settings if needed (default ids for Confluence, other skins will be different)
  * Seeking is not possible (server side)
  * Try not to queue everything at once, one album/artist at a time should be fine.
  * Kodi 18 PAPlayer can crash Kodi if something goes wrong with stream/server  
    To avoid this crash use different player for audio playback eg. VideoPlayer  
    advancedsettings.xml:  
```
    <audio>
    <defaultplayer>VideoPlayer</defaultplayer>
    </audio>
```


