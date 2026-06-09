(defun c:MakeLayers ( / layerList layer)
  (princ "\nCreating drawing layers...")
  
  ;; List structure: (Layer Name . AutoCAD Color Index)
  (setq layerList
    '(
      ("Cantilever Tube_7   part 1" . 1)   ; Red
      ("Cantilever Tube_7   part 2" . 2)   ; Yellow
      ("Cantilever Tube_7   part 3" . 3)   ; Green
      ("Cantilever Tube_7   part 4" . 4)   ; Cyan
      ("Cantilever Tube_7   part 5" . 5)   ; Blue
      ("Cantilever Tube_7   part 6" . 6)   ; Magenta
      ("System Hight"              . 30)  ; Orange
      ("CW Hight"                  . 40)  ; Light Orange/Gold
      ("CW Stagger"                . 80)  ; Lime Green
      ("PRM"                       . 150) ; Sky Blue
      ("Soil level"                . 34)  ; Brownish/Mud
      ("cantilever Hight"          . 210) ; Purple
      ("Measurment on pole"        . 130) ; Teal
      ("pole_rail"                 . 9)   ; Dark Gray
     )
  )

  ;; Loop through the list and generate the layers
  (foreach layer layerList
    (if (not (tblsearch "LAYER" (car layer)))
      (command "-layer" "Make" (car layer) "Color" (cdr layer) "" "")
      (command "-layer" "Color" (cdr layer) (car layer) "") ; Updates color if layer exists
    )
  )

  (princ "\nAll layers created successfully!")
  (princ)
)