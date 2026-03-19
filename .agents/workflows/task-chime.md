---
description: Use this workflow every single time you complete a task to alert the user that you are finished.
---

### Task Completion Notification
When you have fully completed the requested task and require no further action, run the following command to alert the user:

// turbo
```powershell
$file = Get-ChildItem 'C:\Users\kyler\Music\Model Complete Sounds' | Get-Random; if ($file) { (New-Object System.Media.SoundPlayer $file.FullName).PlaySync() }
```
