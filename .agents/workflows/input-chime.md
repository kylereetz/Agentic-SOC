---
description: Use this workflow when you need to alert the user that you are waiting for their input, have hit a roadbump, or need them to look at the IDE.
---

### Attention Required Notification
When you are about to call `notify_user` or are waiting for a command to be approved, run the following command first to alert the user:

// turbo
```powershell
$file = Get-ChildItem 'C:\Users\kyler\Music\Model Complete Sounds' | Get-Random; if ($file) { (New-Object System.Media.SoundPlayer $file.FullName).PlaySync() }
```
