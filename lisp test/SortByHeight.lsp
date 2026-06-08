(defun c:SortByHeight ( / ss i ent polyPts zList maxZ lineData sortedLines rank targetLayer)
  (vl-load-com)
  
  ;; 1. Prompt user to select lines specifically from layer CANTI_7
  (princ "\nSelect the 3D Polylines from layer 'CANTI_7' to rank: ")
  (setq ss (ssget '((0 . "POLYLINE") (8 . "CANTI_7"))))
  
  (if ss
    (progn
      (setq lineData '())
      (setq i 0)
      
      ;; 2. Loop through selected lines to find each line's highest vertex
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        
        ;; Extract flat list of coordinates (X1 Y1 Z1 X2 Y2 Z2 ...)
        (setq polyPts (vlax-safearray->list (vlax-variant-value (vla-get-coordinates (vlax-ename->vla-object ent)))))
        
        ;; Extract just the Z coordinates (every 3rd element starting from index 2)
        (setq zList '())
        (while polyPts
          (setq zList (cons (caddr polyPts) zList))
          (setq polyPts (cdddr polyPts))
        )
        
        ;; Find the maximum Z value for this specific line
        (setq maxZ (apply 'max zList))
        
        ;; Store the entity name paired with its maximum Z value
        (setq lineData (cons (cons ent maxZ) lineData))
        
        (setq i (1+ i))
      )
      
      ;; 3. Sort the lines based on their Max Z value in DESCENDING order (Highest first)
      (setq sortedLines (vl-sort lineData '(lambda (a b) (> (cdr a) (cdr b)))))
      
      ;; 4. Distribute to target layers (CANTI_7_1 to CANTI_7_5) based on rank
      (setq rank 1)
      (foreach item sortedLines
        (setq ent (car item))
        (setq targetLayer (strcat "CANTI_7_" (itoa rank)))
        
        ;; Create the layer if it doesn't exist yet
        (vla-add (vla-get-layers (vla-get-activedocument (vlax-get-acad-object))) targetLayer)
        
        ;; Move the line to its designated rank layer
        (vla-put-layer (vlax-ename->vla-object ent) targetLayer)
        
        (princ (strcat "\nLine with Max Z = " (rtos (cdr item) 2 3) " moved to " targetLayer))
        
        ;; Cap it at 5 layers maximum
        (if (< rank 5)
          (setq rank (1+ rank))
        )
      )
      (princ (strcat "\nSuccessfully sorted " (itoa (length sortedLines)) " lines."))
    )
    (princ "\nNo 3D Polylines selected on layer 'CANTI_7'.")
  )
  (princ)
)

(princ "\nType 'SortByHeight' to run the script.")
(princ)