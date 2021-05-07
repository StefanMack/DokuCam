# DokuCam
Die Digitalisierung in den Schulen und Hochschulen während der Corona-Pandemie hat die Vormachtstellung von Digitalkonzernen wie Microsoft und Google weiter zementiert.  
Aus Steuermitteln wurde allzu oft Hardware gekauft, die nicht mit freien Betriebssystemen wie Linux kompatibel ist. Ein gutes Beispiel hierfür sind die Dokumentenkameras L-12 des Herstellers Elmo. 
  
Doch zum Glück gibt es findige Programmierer, welche das "Reverse Engineering" beherrschen. Und zum Glück hat Elmo das USB-Prokoll zu seiner Dokumentenkamera recht einfach gehalten. Vor vielen Jahren hat Jan Hoersch das Python-Programm [freeElmo](https://nv1t.github.io/blog/freeing-elmo) geschieben, um die Kamera auch mit Linux-Betriebssystem zu betreiben.  

Leider basierte dieser Code noch auf Python 2. Daher wurde für dieses Repository ``freeElmo`` auf Python 3 aktualisiert. Der Code ist trotz seines neuen Namens  ``elmoUi``  weitgehend identisch zum ursprünglichen Code von Jan Hoersch und verwendet weiterhin PyGame als Grafikbibliothek.

![Screenshot elmoUi](/elmoUi_Screenshot.png)

License
-----
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons Lizenzvertrag" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />Dieses Werk ist lizenziert unter einer <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Namensnennung - Weitergabe unter gleichen Bedingungen 4.0 International Lizenz</a>. Most contents of this software were adopted from the GitHub repository [freeElmo](https://github.com/nv1t/freeElmo/)
