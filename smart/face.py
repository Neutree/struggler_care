# Download model from: https://www.maixhub.com/index.php/index/index/detail/id/235
import sensor,image,lcd
import KPU as kpu
import time
from Maix import FPIOA,GPIO


class Face_Recog:
    def __init__(self):
        self._m_fd = kpu.load(0x200000)
        self._m_ld = kpu.load(0x300000)
        self._m_fe = kpu.load(0x400000)
        self._anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
        self._dst_point = [(44,59),(84,59),(64,82),(47,105),(81,105)]
        self.names = []
        self.features = []
        _ = kpu.init_yolo2(self._m_fd, 0.5, 0.3, 5, self._anchor)
        self.img_face=image.Image(size=(128,128))
        _ = self.img_face.pix_to_ai()
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        # sensor.set_hmirror(1)
        sensor.set_vflip(1)
        self.show_img_timeout = 5
        self._show_img_t = -5
    
    def __del__(self):
        _ = kpu.deinit(self._m_fe)
        _ = kpu.deinit(self._m_ld)
        _ = kpu.deinit(self._m_fd)

    def set_users(self, names, features):
        self.names = names
        self.features
    
    def get_users(self):
        return self.names, self.features

    def run(self, on_detect, on_img, on_clear, on_people=None, always_show_img=False):
        img = sensor.snapshot()
        try:
            code = kpu.run_yolo2(self._m_fd, img)
        except Exception:
            return
        if code:
            for i in code:
                a = img.draw_rectangle(i.rect())
                face_cut = img.cut(i.x(),i.y(),i.w(),i.h())
                face_cut_128 = face_cut.resize(128,128)
                a = face_cut_128.pix_to_ai()
                #a = img.draw_image(face_cut_128, (0,0))
                # Landmark for face 5 points
                try:
                    fmap = kpu.forward(self._m_ld, face_cut_128)
                except Exception:
                    continue
                plist=fmap[:]
                le=(i.x()+int(plist[0]*i.w() - 10), i.y()+int(plist[1]*i.h()))
                re=(i.x()+int(plist[2]*i.w()), i.y()+int(plist[3]*i.h()))
                nose=(i.x()+int(plist[4]*i.w()), i.y()+int(plist[5]*i.h()))
                lm=(i.x()+int(plist[6]*i.w()), i.y()+int(plist[7]*i.h()))
                rm=(i.x()+int(plist[8]*i.w()), i.y()+int(plist[9]*i.h()))
                a = img.draw_circle(le[0], le[1], 4)
                a = img.draw_circle(re[0], re[1], 4)
                a = img.draw_circle(nose[0], nose[1], 4)
                a = img.draw_circle(lm[0], lm[1], 4)
                a = img.draw_circle(rm[0], rm[1], 4)
                # align face to standard position
                src_point = [le, re, nose, lm, rm]
                T=image.get_affine_transform(src_point, self._dst_point)
                a=image.warp_affine_ai(img, self.img_face, T)
                a=self.img_face.ai_to_pix()
                #a = img.draw_image(img_face, (128,0))
                del(face_cut_128)
                # calculate face feature vector
                try:
                    fmap = kpu.forward(self._m_fe, self.img_face)
                except Exception:
                    continue
                feature=kpu.face_encode(fmap[:])
                scores = []
                for j in range(len(self.features)):
                    score = kpu.face_compare(self.features[j], feature)
                    scores.append(score)
                max_score = 0
                index = 0
                for k in range(len(scores)):
                    if max_score < scores[k]:
                        max_score = scores[k]
                        index = k
                if max_score > 85:
                    a = img.draw_string(i.x(),i.y(), ("%s :%2.1f" % (self.names[index], max_score)), color=(0,255,0),scale=2)
                    on_detect(self.names[index], feature, max_score, img)
                else:
                    # a = img.draw_string(i.x(),i.y(), ("X :%2.1f" % (max_score)), color=(255,0,0),scale=2)
                    on_img(img)
                if on_people:
                    on_people(feature, img)
                self._show_img_t = time.ticks_ms() / 1000.0
        else:
            if always_show_img:
                on_img(img)
            else:
                if time.ticks_ms() - self._show_img_t * 1000 < self.show_img_timeout * 1000:
                    on_img(img)
                else:
                    on_clear()
            

if __name__ == "__main__":
    face = Face_Recog()
    lcd.init()
    def on_detect(user, feature, score, img):
        print(user, feature, score)
        lcd.display(img)
    def on_img(img):
        lcd.display(img)
    def on_clear():
        lcd.clear()

    while 1:
        face.run(on_detect, on_img, on_clear)
