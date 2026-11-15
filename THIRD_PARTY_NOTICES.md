# Third-party notices for SuperCALC firmware

This file accompanies the SuperCALC UF2 for the ClockworkPi PicoCalc (Raspberry Pi Pico 2 W). The UF2 is a compiled binary that includes third-party software. SuperCALC's own code is licensed separately under the MIT License (see `LICENSE` in the SuperCALC repository). This file does **not** change those third-party terms.

**Hardware limit:** the cyw43-driver and BTstack portions of this firmware may be used and redistributed only with Raspberry Pi Ltd semiconductor devices (here, the Pico 2 W / RP2350 and its CYW43439 radio). Do not flash or ship this UF2 for use on a non-Raspberry Pi microcontroller.

Pinned sources used to build this firmware:

- MicroPython `f187c77da8b0ff51927b62cd1f4efd78c03bdb7f` (v1.25.0-preview.389)
- zenodante/eigenmath_micropython `ea94bc5a9565f0565e04218061237096f6e0ca54`
- LofiFren/PicoCalc `c711a366febe21061dbfff69a616cb22e0364ccd` (MIT LICENSE file added in the following commit, `870e0f24896bd28fc0bc68c22c2aca68327b2326`)

---

## 1. MicroPython

Copyright (c) 2013-2025 Damien P. George

https://github.com/micropython/micropython/tree/f187c77da8b0ff51927b62cd1f4efd78c03bdb7f

SPDX: MIT

```
The MIT License (MIT)

Copyright (c) 2013-2025 Damien P. George

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

Individual MicroPython files may include additional copyright holders. Port-specific third-party components actually linked into the Pico 2 W binary are listed below. (L)GPL tools mentioned in MicroPython's top-level LICENSE are used only at build time and are not part of the UF2.

---

## 2. Raspberry Pi Pico SDK

Copyright 2020 (c) 2020 Raspberry Pi (Trading) Ltd.

https://github.com/raspberrypi/pico-sdk/tree/bddd20f928ce76142793bef434d4f75f4af6e433 (v2.1.1)

SPDX: BSD-3-Clause

```
Copyright 2020 (c) 2020 Raspberry Pi (Trading) Ltd.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### 2.1 pico_printf

The MIT License (MIT)

Copyright (c) 2014 Marco Paland

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## 3. TinyUSB

The MIT License (MIT)

Copyright (c) 2018, hathach (tinyusb.org)

https://github.com/hathach/tinyusb/tree/5217cee5de4cd555018da90f9f1bcc87fb1c1d3a

SPDX: MIT

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## 4. cyw43-driver and CYW43 firmware (Wi-Fi / Bluetooth radio)

Copyright (C) 2019-2022 George Robotics Pty Ltd

https://github.com/georgerobotics/cyw43-driver/tree/dd7568229f3bf7a37737b9e1ef250c26efe75b23

This firmware is built for a Raspberry Pi Pico 2 W, so the applicable grant is **LICENSE.RP**, not the non-commercial license. Both texts are reproduced so the alternative grant is on the record.

### 4.1 LICENSE.RP (applicable on Pico 2 W)

```
Copyright (C) 2019-2022 George Robotics Pty Ltd

Raspberry Pi Ltd (Licensor) hereby grants to you a non-exclusive license to
use this software solely with the Licensor's microcontroller chip (RP2040) or
any other semiconductor device produced by the Licensor. No other use is
permitted under the terms of this licence.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. The software can only be used and redistributed in conjunction with RP2040
   or any other semiconductor device produced by the Licensor.
2. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
3. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE LICENSOR AND COPYRIGHT OWNER "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE LICENSOR OR COPYRIGHT OWNER BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This software is also available from the copyright owner under different
terms (see ./LICENSE)
```

### 4.2 Non-commercial alternative (NOT the grant used for this Pico 2 W UF2)

```
Copyright (C) 2019-2022 George Robotics Pty Ltd

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Any redistribution, use, or modification in source or binary form is done
   solely for personal benefit and not for any commercial purpose or for
   monetary gain.

THIS SOFTWARE IS PROVIDED BY THE LICENSOR AND COPYRIGHT OWNER "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE LICENSOR OR COPYRIGHT OWNER BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This software is also available for use with Raspberry Pi Ltd semiconductor
devices under different terms (see ./LICENSE.RP).

For commercial licensing options please email contact@georgerobotics.com.au
```

### 4.3 Infineon / Cypress Wi-Fi and Bluetooth firmware blobs

The combined CYW43439 firmware and Bluetooth patch blobs in `cyw43-driver/firmware/` are third-party binary images that the host loads onto the radio. They are also commonly redistributed under the Infineon/Cypress Permissive Binary License 1.0:

```
Permissive Binary License

Version 1.0, July 2019

Redistribution. Redistribution and use in binary form, without
modification, are permitted provided that the following conditions are
met:

1) Redistributions must reproduce the above copyright notice and the
 following disclaimer in the documentation and/or other materials
 provided with the distribution.

2) Unless to the extent explicitly permitted by law, no reverse
 engineering, decompilation, or disassembly of this software is
 permitted.

3) Redistribution as part of a software development kit must include the
 accompanying file named "DEPENDENCIES" and any dependencies listed in
 that file.

4) Neither the name of the copyright holder nor the names of its
 contributors may be used to endorse or promote products derived from
 this software without specific prior written permission.

Limited patent license. The copyright holders (and contributors) grant a
worldwide, non-exclusive, no-charge, royalty-free patent license to
make, have made, use, offer to sell, sell, import, and otherwise
transfer this software, where such license applies only to those patent
claims licensable by the copyright holders (and contributors) that are
necessarily infringed by this software. This patent license shall not
apply to any combinations that include this software. No hardware is
licensed hereunder.

If you institute patent litigation against any entity (including a
cross-claim or counterclaim in a lawsuit) alleging that the software
itself infringes your patent(s), then your rights granted under this
license shall terminate as of the date such litigation is filed.

DISCLAIMER. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS." ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

## 5. BTstack

Copyright (C) 2009 BlueKitchen GmbH

https://github.com/bluekitchen/btstack/tree/77e752abd6a0992334047a48038a5a3960e5c6bc

The default BlueKitchen license is non-commercial. This Pico 2 W build uses the Raspberry Pi grant in pico-sdk `src/rp2_common/pico_btstack/LICENSE.RP`, which is the applicable license for this UF2.

### 5.1 Raspberry Pi / BlueKitchen grant (applicable on Pico 2 W)

```
"BlueKitchen" shall refer to BlueKitchen GmbH.
"Raspberry Pi" shall refer to Raspberry Pi Ltd.
"Product" shall refer to Raspberry Pi hardware products Pico W, Pico WH, Pico 2 W, Pico 2 WH, and RM2.
"Customer" means any purchaser of a Product.
"Customer Products" means products manufactured or distributed by Customers which use or are derived from Products.

Raspberry Pi grants to the Customer a non-exclusive, non-transferable, non-sublicensable, irrevocable, perpetual
and worldwide licence to use, copy, store, develop, modify, and transmit BTstack in order to use BTstack with or
integrate BTstack into Products or Customer Products, and distribute BTstack as part of these Products or
Customer Products or their related documentation or SDKs.

All use of BTstack by the Customer is limited to Products or Customer Products, and the Customer represents and
warrants that all such use shall be in compliance with the terms of this licence and all applicable laws and
regulations, including but not limited to, copyright and other intellectual property laws and privacy regulations.

BlueKitchen retains all rights, title and interest in, to and associated with BTstack and associated websites.
Customer shall not take any action inconsistent with BlueKitchen's ownership of BTstack, any associated services,
websites and related content.

There are no implied licences under the terms set forth in this licence, and any rights not expressly granted
hereunder are reserved by BlueKitchen.

BTSTACK IS PROVIDED BY RASPBERRY PI "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED TO THE FULLEST EXTENT
PERMISSIBLE UNDER APPLICABLE LAW. IN NO EVENT SHALL RASPBERRY PI OR BLUEKITCHEN BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF BTSTACK, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### 5.2 Default BlueKitchen license (NOT the grant used for this Pico 2 W UF2)

```
Copyright (C) 2009 BlueKitchen GmbH
All rights reserved

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holders nor the names of
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

4. Any redistribution, use, or modification is done solely for
   personal benefit and not for any commercial purpose or for
   monetary gain.

THIS SOFTWARE IS PROVIDED BY BLUEKITCHEN GMBH AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL BLUEKITCHEN
GMBH OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.

Please inquire about commercial licensing options at
contact@bluekitchen-gmbh.com
```

### 5.3 micro-ecc (used by BTstack)

Copyright (c) 2014, Kenneth MacKay  
All rights reserved.

SPDX: BSD-2-Clause

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---

## 6. lwIP

Copyright (c) 2001, 2002 Swedish Institute of Computer Science.  
All rights reserved.

https://github.com/lwip-tcpip/lwip (commit `0a0452b2c39bdd91e252aef045c115f88f6ca773`)

SPDX: BSD-3-Clause

```
Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
```

---

## 7. Mbed TLS

Copyright The Mbed TLS Contributors

https://github.com/Mbed-TLS/mbedtls/tree/107ea89daaefb9867ea9121002fbbdf926780e98

Mbed TLS is dual-licensed Apache-2.0 OR GPL-2.0-or-later. This SuperCALC binary takes the code under **Apache License 2.0** only. The full Apache-2.0 text is required to be provided with the distribution; place a copy at `LICENSES/Apache-2.0.txt` in the release, or see https://www.apache.org/licenses/LICENSE-2.0

SPDX: Apache-2.0

---

## 8. littlefs

Copyright (c) 2022, The littlefs authors.  
Copyright (c) 2017, Arm Limited. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause

Upstream: https://github.com/littlefs-project/littlefs (MicroPython vendors an lfs2-prefixed copy of v2.3.0).

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---

## 9. FatFs / ooFatFs

Copyright (C) 2018, ChaN, all right reserved.

FatFs - Generic FAT Filesystem Module R0.13c, as customised by MicroPython (`lib/oofatfs`).

```
FatFs module is an open source software. Redistribution and use of FatFs in
source and binary forms, with or without modification, are permitted provided
that the following condition is met:

1. Redistributions of source code must retain the above copyright notice,
   this condition and the following disclaimer.

This software is provided by the copyright holder and contributors "AS IS"
and any warranties related to this software are DISCLAIMED.
The copyright owner or contributors be NOT LIABLE for any damages caused
by use of this software.
```

---

## 10. uzlib

uzlib - tiny deflate/inflate library

Copyright (c) 2003 by Joergen Ibsen / Jibz. All Rights Reserved.  
http://www.ibsensoftware.com/  
Copyright (c) 2014-2018 by Paul Sokolovsky  
Optimised for MicroPython: Copyright (c) 2023 by Jim Mussared

SPDX: Zlib

```
This software is provided 'as-is', without any express
or implied warranty.  In no event will the authors be
held liable for any damages arising from the use of
this software.

Permission is granted to anyone to use this software
for any purpose, including commercial applications,
and to alter it and redistribute it freely, subject to
the following restrictions:

1. The origin of this software must not be
   misrepresented; you must not claim that you
   wrote the original software. If you use this
   software in a product, an acknowledgment in
   the product documentation would be appreciated
   but is not required.

2. Altered source versions must be plainly marked
   as such, and must not be misrepresented as
   being the original software.

3. This notice may not be removed or altered from
   any source distribution.
```

---

## 11. re1.5 (MicroPython `re` module)

Copyright 2007-2009 Russ Cox. All Rights Reserved.  
Copyright 2014 Paul Sokolovsky.

Classified as BSD-3-Clause in MicroPython's top-level LICENSE. Use of this source code is governed by a BSD-style license as stated in the file headers.

---

## 12. Math library (musl and SunPro fdlibm)

### 12.1 musl (libm_dbl, used in the double-precision SuperCALC build)

Copyright © 2005-2014 Rich Felker, et al.

From musl v1.1.16. SPDX: MIT

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### 12.2 SunPro fdlibm

```
Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.

Developed at SunPro, a Sun Microsystems, Inc. business.
Permission to use, copy, modify, and distribute this
software is freely granted, provided that this notice
is preserved.
```

---

## 13. crypto-algorithms (SHA-256)

Source: https://github.com/B-Con/crypto-algorithms  
Author: Brad Conte  
This code is released into the public domain.

---

## 14. eigenmath (George Weigt)

BSD 2-Clause License

Copyright (c) 2024, George Weigt  
All rights reserved.

https://github.com/georgeweigt/eigenmath

```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

The MicroPython binding used in this firmware is the port at https://github.com/zenodante/eigenmath_micropython/tree/ea94bc5a9565f0565e04218061237096f6e0ca54. The `eigenmath.c` core carries the license above. **The wrapper files (`eigenmath_mpy.c`, `eheap.c`) and the port repository currently have no license grant.** A public release should wait until zenodante licenses that port, then add the grant here.

---

## 15. LofiFren PicoCalc modules

MIT License

Copyright (c) 2026 Lofi Fren

https://github.com/LofiFren/PicoCalc  
Pin used in the SuperCALC build: `c711a366febe21061dbfff69a616cb22e0364ccd`  
LICENSE file: added in `870e0f24896bd28fc0bc68c22c2aca68327b2326`

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

LofiFren's README credits the display driver, keyboard logic, and original 1.0 UF2 to zenodante's [PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver). That upstream repository currently has **no license**. LofiFren's MIT grant covers LofiFren's own work (including `picosampler` and later patches). It does not replace a license from zenodante for the inherited driver code.

---

## 16. vt100_stm32 (ancestor of vtterminal)

MIT License

Copyright (c) 2018 Hideaki Tominaga

https://github.com/ht-deko/vt100_stm32

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

The 6×8 “SHARP PC-E500 style” fonts in `font6x8.h` / `font6x8e500.h` arrived through this tree. No separate font license was found.

---

## 17. sdcard.py (if shipped with the firmware or `/modules`)

From [micropython-lib](https://github.com/micropython/micropython-lib) (`micropython/drivers/storage/sdcard`). Files in micropython-lib that do not state otherwise are under the MIT License:

Copyright (c) 2013, 2014 micropython-lib contributors

The MIT permission notice is the same as in section 1.

---

## 18. C runtime (newlib-nano)

The UF2 is linked with newlib-nano from the ARM GNU Toolchain. newlib is a collection of historically BSD-style and other notices (see the toolchain's `COPYING.NEWLIB`). Those notices apply to the C runtime linked into this binary.

---

## 19. Hardware acknowledgement

SuperCALC targets the ClockworkPi PicoCalc. Official PicoCalc sources at https://github.com/clockworkpi/PicoCalc have no repository-wide license and are **not** included in this firmware. ClockworkPi is credited for the hardware.

---

## 20. Outstanding clearances (do not ignore)

Before this notices file is published with a UF2:

1. Obtain a license from zenodante for PicoCalc-micropython-driver and for the eigenmath_micropython wrapper, and paste it into this file.
2. Do not ship the modified `pye.py` (robert-hh/Micropython-Editor has no license) unless that project is licensed.
3. Bundle the full Apache-2.0 text for Mbed TLS (`LICENSES/Apache-2.0.txt`).
