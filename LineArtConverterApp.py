import tkinter as tk
from tkinter import filedialog, messagebox, Scale, IntVar
from PIL import Image, ImageTk
import cv2
import numpy as np

class LineArtConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("線画変換アプリ")
        master.geometry("900x700") # 初期ウィンドウサイズを少し広げることも検討

        self.original_image_pil = None
        self.line_art_image_pil = None
        self.image_path = None

        self.target_original_display_width = 400
        self.target_original_display_height = 300
        self.target_line_art_display_width = 400
        self.target_line_art_display_height = 300

        # --- UI要素の作成 ---
        control_frame = tk.Frame(master)
        control_frame.pack(pady=10)

        self.btn_load = tk.Button(control_frame, text="画像を選択", command=self.load_image, width=15)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_convert = tk.Button(control_frame, text="線画化実行", command=lambda: self.convert_to_line_art(auto_call=False), state=tk.DISABLED, width=15)
        self.btn_convert.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(control_frame, text="線画を保存", command=self.save_line_art, state=tk.DISABLED, width=15)
        self.btn_save.pack(side=tk.LEFT, padx=5)

        param_frame = tk.Frame(master)
        param_frame.pack(pady=5)

        tk.Label(param_frame, text="Canny閾値1:").pack(side=tk.LEFT)
        self.canny_thresh1_var = IntVar(value=50)
        self.canny_thresh1_scale = Scale(param_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.canny_thresh1_var, length=120, command=self.on_param_change) # length調整
        self.canny_thresh1_scale.pack(side=tk.LEFT, padx=5)

        tk.Label(param_frame, text="Canny閾値2:").pack(side=tk.LEFT)
        self.canny_thresh2_var = IntVar(value=150)
        self.canny_thresh2_scale = Scale(param_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.canny_thresh2_var, length=120, command=self.on_param_change) # length調整
        self.canny_thresh2_scale.pack(side=tk.LEFT, padx=5)

        tk.Label(param_frame, text="線の太さ:").pack(side=tk.LEFT)
        self.line_thickness_var = IntVar(value=2) # デフォルトの太さを2に設定
        self.line_thickness_scale = Scale(param_frame, from_=1, to=10, orient=tk.HORIZONTAL, variable=self.line_thickness_var, length=100, command=self.on_param_change)
        self.line_thickness_scale.pack(side=tk.LEFT, padx=5)

        image_display_frame = tk.Frame(master)
        image_display_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        image_display_frame.grid_columnconfigure(0, weight=1)
        image_display_frame.grid_columnconfigure(1, weight=1)
        image_display_frame.grid_rowconfigure(0, weight=1)

        self.original_image_label_frame = tk.LabelFrame(image_display_frame, text="元画像", padx=5, pady=5)
        self.original_image_label_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.lbl_original_image = tk.Label(self.original_image_label_frame)
        self.lbl_original_image.pack(expand=True, fill=tk.BOTH)

        self.line_art_label_frame = tk.LabelFrame(image_display_frame, text="線画", padx=5, pady=5)
        self.line_art_label_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.lbl_line_art_image = tk.Label(self.line_art_label_frame)
        self.lbl_line_art_image.pack(expand=True, fill=tk.BOTH)

        self.master.bind("<Configure>", self.on_resize)
        self._resize_timer = None
        self.master.after(100, self._initial_size_update)

    def _initial_size_update(self):
        self.master.update_idletasks()
        self.target_original_display_width = max(1, self.original_image_label_frame.winfo_width() - 10)
        self.target_original_display_height = max(1, self.original_image_label_frame.winfo_height() - 10)
        self.target_line_art_display_width = max(1, self.line_art_label_frame.winfo_width() - 10)
        self.target_line_art_display_height = max(1, self.line_art_label_frame.winfo_height() - 10)
        
        if self.original_image_pil:
             self._update_image_display(self.original_image_pil, self.lbl_original_image,
                                       self.target_original_display_width, self.target_original_display_height)
        if self.line_art_image_pil:
             self._update_image_display(self.line_art_image_pil, self.lbl_line_art_image,
                                       self.target_line_art_display_width, self.target_line_art_display_height)

    def load_image(self):
        self.image_path = filedialog.askopenfilename(
            title="画像ファイルを選択",
            filetypes=(("画像ファイル", "*.jpg;*.jpeg;*.png;*.bmp;*.gif"),
                       ("JPEG files", "*.jpg;*.jpeg"),
                       ("PNG files", "*.png"),
                       ("All files", "*.*"))
        )
        if not self.image_path:
            return

        try:
            self.original_image_pil = Image.open(self.image_path)
            self.master.update_idletasks() 

            current_original_frame_width = max(1, self.original_image_label_frame.winfo_width() - 10)
            current_original_frame_height = max(1, self.original_image_label_frame.winfo_height() - 10)
            self.target_original_display_width = current_original_frame_width
            self.target_original_display_height = current_original_frame_height

            self._update_image_display(self.original_image_pil, self.lbl_original_image,
                                       self.target_original_display_width, self.target_original_display_height)

            current_lineart_frame_width = max(1, self.line_art_label_frame.winfo_width() - 10)
            current_lineart_frame_height = max(1, self.line_art_label_frame.winfo_height() - 10)
            self.target_line_art_display_width = current_lineart_frame_width
            self.target_line_art_display_height = current_lineart_frame_height
            
            self.btn_convert["state"] = tk.NORMAL
            self.btn_save["state"] = tk.DISABLED
            self.lbl_line_art_image.config(image='')
            self.line_art_image_pil = None
            self.on_param_change()
        except Exception as e:
            messagebox.showerror("エラー", f"画像を開けませんでした: {e}")
            self.original_image_pil = None
            self.btn_convert["state"] = tk.DISABLED

    def _update_image_display(self, pil_image, label_widget, target_width, target_height):
        if pil_image:
            current_target_width = max(target_width, 50) 
            current_target_height = max(target_height, 50)

            img_copy = pil_image.copy()
            try:
                img_copy.thumbnail((current_target_width, current_target_height), Image.Resampling.LANCZOS)
            except AttributeError:
                img_copy.thumbnail((current_target_width, current_target_height), Image.LANCZOS)

            img_tk = ImageTk.PhotoImage(img_copy)
            label_widget.config(image=img_tk)
            label_widget.image = img_tk 
        else:
            label_widget.config(image='')

    def convert_to_line_art(self, auto_call=False):
        if not self.original_image_pil:
            if not auto_call:
                 messagebox.showwarning("警告", "まず画像を選択してください。")
            return

        try:
            open_cv_image = cv2.cvtColor(np.array(self.original_image_pil), cv2.COLOR_RGB2BGR)
            gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            
            thresh1 = self.canny_thresh1_var.get()
            thresh2 = self.canny_thresh2_var.get()
            edges = cv2.Canny(gray_image, thresh1, thresh2)

            # --- 線を太くする処理 ---
            thickness = self.line_thickness_var.get()
            if thickness > 0: # スケールの最小値は1なので、常に > 0
                # スケール値が1の場合、1x1カーネルとなり、元のCannyの線とほぼ同じ太さになる
                # スケール値が2以上の場合、線が太くなる
                kernel_size = thickness 
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                dilated_edges = cv2.dilate(edges, kernel, iterations=1)
                line_art_cv = cv2.bitwise_not(dilated_edges)
            else:
                line_art_cv = cv2.bitwise_not(edges)
            # --- 太くする処理ここまで ---
            
            self.line_art_image_pil = Image.fromarray(line_art_cv)

            self._update_image_display(self.line_art_image_pil, self.lbl_line_art_image,
                                       self.target_line_art_display_width, self.target_line_art_display_height)
            self.btn_save["state"] = tk.NORMAL

        except Exception as e:
            if not auto_call:
                messagebox.showerror("エラー", f"線画変換中にエラーが発生しました: {e}")
            self.line_art_image_pil = None
            self.btn_save["state"] = tk.DISABLED

    def on_param_change(self, event=None):
        if self.original_image_pil and self.btn_convert["state"] == tk.NORMAL:
            self.convert_to_line_art(auto_call=True)

    def save_line_art(self):
        if not self.line_art_image_pil:
            messagebox.showwarning("警告", "保存する線画がありません。")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=(("PNG files", "*.png"),
                       ("JPEG files", "*.jpg"),
                       ("BMP files", "*.bmp"),
                       ("All files", "*.*")),
            title="線画を保存"
        )
        if not save_path:
            return

        try:
            self.line_art_image_pil.save(save_path)
            messagebox.showinfo("成功", f"線画を {save_path} に保存しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました: {e}")

    def on_resize(self, event=None):
        if self._resize_timer:
            self.master.after_cancel(self._resize_timer)
        self._resize_timer = self.master.after(250, self._redraw_images_on_resize) 

    def _redraw_images_on_resize(self):
        self.master.update_idletasks() 

        self.target_original_display_width = max(1, self.original_image_label_frame.winfo_width() - 10)
        self.target_original_display_height = max(1, self.original_image_label_frame.winfo_height() - 10)
        self.target_line_art_display_width = max(1, self.line_art_label_frame.winfo_width() - 10)
        self.target_line_art_display_height = max(1, self.line_art_label_frame.winfo_height() - 10)

        if self.original_image_pil:
            self._update_image_display(self.original_image_pil, self.lbl_original_image,
                                       self.target_original_display_width, self.target_original_display_height)
        if self.line_art_image_pil:
            self._update_image_display(self.line_art_image_pil, self.lbl_line_art_image,
                                       self.target_line_art_display_width, self.target_line_art_display_height)

def main():
    root = tk.Tk()
    app = LineArtConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()