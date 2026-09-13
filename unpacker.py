import sys

from Source.UI.ui_old import UIOld
from Source.UI.ui_tkinter import UITkinter

if __name__ == '__main__':
    _type = sys.argv[1] if len(sys.argv) > 1 else None
    
    if _type is None or _type.lower() == "new":
        app = UITkinter()
        app.mainloop()
    elif _type.lower() == "old":
        app = UIOld()
        app.mainloop()
    
