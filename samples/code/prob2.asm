; https://medium.com/@TheZaki/project-euler-2-even-fibonacci-numbers-2219e9438970

; r1 - n - 2
; r2 - n - 1
; r3 - n
; r4 - answer
; r5 - 400000


_start:     add r1, r0, 2
            add r2, r0, 8
            add r4, r0, 10
            add r5, r0, 4000000
loop:       mul r3, r2, 4
            add r3, r3, r1
            bge r3, r5, end

            add r4, r4, r3
            add r1, r0, r2
            add r2, r0, r3
            jmp loop
end:        out r4, 0
            hlt
