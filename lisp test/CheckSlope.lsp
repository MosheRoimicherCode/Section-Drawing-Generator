(defun c:CheckSlope ( / ent polyPts pt1 pt2 dx dy dz run slope pctStr ratioStr )
  (vl-load-com)
  
  ;; 1. Prompt user to select a single 3D Polyline
  (setq ent (car (entsel "\nSelect a 3D Polyline to analyze slope: ")))
  
  (if ent
    (progn
      ;; Check if the selected object is a Polyline
      (if (= (cdr (assoc 0 (entget ent))) "POLYLINE")
        (progn
          ;; Extract coordinates using Visual LISP ActiveX
          (setq polyPts (vlax-safearray->list (vlax-variant-value (vla-get-coordinates (vlax-ename->vla-object ent)))))
          
          ;; Ensure we have at least two 3D points (6 coordinates)
          (if (>= (length polyPts) 6)
            (progn
              ;; Grab start and end vertices
              (setq pt1 (list (nth 0 polyPts) (nth 1 polyPts) (nth 2 polyPts)))
              (setq pt2 (list (nth 3 polyPts) (nth 4 polyPts) (nth 5 polyPts)))
              
              ;; Calculate Delta X, Delta Y, and Delta Z (Rise)
              (setq dx (- (car pt2) (car pt1)))
              (setq dy (- (cadr pt2) (cadr pt1)))
              (setq dz (abs (- (caddr pt2) (caddr pt1))))
              
              ;; Calculate horizontal 2D distance (Run)
              (setq run (sqrt (+ (* dx dx) (* dy dy))))
              
              (if (> run 0.0)
                (progn
                  ;; Calculate slope and strings
                  (setq slope (/ dz run))
                  (setq pctStr (rtos (* slope 100.0) 2 3))   ; 3 decimal places for precision
                  
                  (if (> slope 0.0)
                    (setq ratioStr (strcat "1:" (rtos (/ 1.0 slope) 2 2)))
                    (setq ratioStr "Flat")
                  )
                  
                  ;; 2. Print beautifully formatted data to the CLI
                  (textscr) ; Optional: Pops open the expanded text window so you can read it easily
                  (princ "\n========================================")
                  (princ "\n      3D POLYLINE SLOPE ANALYSIS        ")
                  (princ "\n----------------------------------------")
                  (princ (strcat "\n SLOPE PERCENTAGE     : " pctStr "%"))
                  (princ "\n========================================")
                )
                (princ "\nError: Line has a horizontal length of zero (perfectly vertical line).")
              )
            )
            (princ "\nError: Polyline does not have enough vertex data.")
          )
        )
        (princ "\nSelected object is not a 3D Polyline.")
      )
    )
  )
  (princ)
)

(princ "\nType 'CheckSlope' to run the script.")
(princ)