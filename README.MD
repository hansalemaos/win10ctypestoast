# Windows-10-Toast-Notifications without pywin32 dependency

## pip install win10ctypestoast

### Tested against Windows 10 / Python 3.10 / Anaconda 

#### Basically the same as https://github.com/jithurjacob/Windows-10-Toast-Notifications
#### but without pywin32 dependency.

```python
from win10ctypestoast import show_toast

show_toast(
    title="Title",
    message="Message",
    icon=r"C:\Users\hansc\Pictures\numberresults.png",
    duration=1,
    repeat=2,
    pause=2,
    threaded=False,
)
show_toast(
    title="Title",
    message="Message",
    icon=r"C:\Users\hansc\Pictures\numberresults.png",
    duration=2,
    repeat=2,
    pause=1,
    threaded=True,
)



```