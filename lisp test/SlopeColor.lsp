(defun c:SlopeColor ( / layName ss i ent polyPts pt1 pt2 dx dy run dz slope col)
  (vl-load-com)
  
  ;; 1. Get user input for the target layer
  (setq layName (getstring t "\nEnter the exact Layer Name to analyze: "))
  
  ;; 2. Select all 3D Polylines on that specific layer
  (setq ss (ssget "X" (list '(0 . "POLYLINE") (cons 8 layName))))
  
  (if ss
    (progn
      (setq i 0)
      ;; 3. Loop through each found 3D Polyline
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        
        ;; Extract coordinates using Visual LISP ActiveX
        (setq polyPts (vlax-safearray->list (vlax-variant-value (vla-get-coordinates (vlax-ename->vla-object ent)))))
        
        ;; Ensure we have at least two 3D points (6 coordinates: X1, Y1, Z1, X2, Y2, Z2)
        (if (>= (length polyPts) 6)
          (progn
            ;; Grab the first vertex
            (setq pt1 (list (nth 0 polyPts) (nth 1 polyPts) (nth 2 polyPts)))
            ;; Grab the second vertex
            (setq pt2 (list (nth 3 polyPts) (nth 4 polyPts) (nth 5 polyPts)))
            
            ;; Calculate Delta X, Delta Y, and Delta Z
            (setq dx (- (car pt2) (car pt1)))
            (setq dy (- (cadr pt2) (cadr pt1)))
            (setq dz (abs (- (caddr pt2) (caddr pt1))))
            
            ;; Calculate horizontal 2D distance (Run)
            (setq run (sqrt (+ (* dx dx) (* dy dy))))
            
            ;; Avoid division by zero for perfectly vertical or glitchy lines
            (if (> run 0.0)
              (progn
                ;; Calculate slope percentage: (Rise / Run) * 100
                (setq slope (* (/ dz run) 100.0))
                
                ;; 4. Categorize slope into 4 distinct ranges and assign AutoCAD Color Index (ACI)
                (cond
                  ((<= slope 1.0)                  (setq col 1)) ; Range 1: 0% - 2% (Red)
                  ((and (> slope 3.0) (<= slope 10.0))  (setq col 2)) ; Range 2: 2% - 5% (Yellow)
                  ((and (> slope 5.0) (<= slope 20.0)) (setq col 3)) ; Range 3: 5% - 10% (Green)
                  ((> slope 30.0)                 (setq col 6)) ; Range 4: > 10% (Magenta)
                )
                
                ;; Apply the color to the entity
                (command "._chprop" ent "" "_color" col "")
              )
            )
          )
        )
        (setq i (1+ i))
      )
      (princ (strcat "\nSuccess! Processed " (itoa (sslength ss)) " 3D polylines on layer '" layName "'."))
    )
    (princ (strcat "\nNo 3D Polylines found on layer '" layName "'."))
  )
  (princ)
)

(princ "\nType 'SlopeColor' to run the script.")
(princ)