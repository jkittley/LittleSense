# Little Sense
`settings.py` is well documented and changes should be made in accordance with the comments. `secure.py` contains settings which should not be shared on a public repositiory. Settings are divided into a number of classes. LocalSetting, RemoteSettings and TestSettings all inherit from DefaultSetting which inturn inherits from SecureSettings. What does this mean?

- Any setting in DefaultSetting and SecureSettings is automatically avalable in LocalSetting, RemoteSettings and TestSettings. 
- Any of the DefaultSetting and SecureSettings can be overwitten by LocalSetting, RemoteSettings or TestSettings. 
- When the environmental variable "LOCAL" is set to True the LocalSetting settings class is returned when `from config import settings` is used in any script.
- When the environmental variable "LOCAL" is not set to True the RemoteSettings are used. 
- If the environmental variable "TESTING" is set to True, then the TestSettings are used. 