function [T_down,PDD_in,PDD_out,gradient]=uta_downscaling(T,elev,elev2,elevi,mask,gradient,half_a_box,stddev,PP_o,lapse_v)
%allow for variable stddev

    T_down=T*NaN;
    lapse=T*NaN;

    half_a_boxx=round(0.8*half_a_box);
    half_a_boxy=round(half_a_box);
    [LX,LY]=size(mask);

    %T(find(mask<=0))=NaN;
    %T(find(elev<0))=NaN;axes
    gradx_int = diff([zeros(1,110);elevi])+diff([elevi;zeros(1,110)]);
    grady_int = diff([zeros(60,1) elevi],1,2)+diff([elevi zeros(60,1)],1,2);
    slope_int = sqrt(gradx_int.^2+grady_int.^2);
    bla='downscaling temperature'
    for j = (1+half_a_boxy:(LY-half_a_boxy))
        for (i = 1+half_a_boxx : (LX-half_a_boxx))
            if (mask(i,j))
                if (length(find(~isnan(T(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy))))>0)
                    min_height2 = nanumin(elev2(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy));
                    min_height = nanumin(elev(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy));
                    max_height2 = nanumax(elev2(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy));
                    min_value = nanumin(T(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy));
                    max_value = nanumax(T(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy));

                    if ( j == (1 + half_a_boxy))
                        left_k = -half_a_boxy;
                        right_k = 0;
                    else if ( j == (LY - half_a_boxy))
                            left_k = 0;
                            right_k = half_a_boxy;
                    else
                        left_k = 0;
                        right_k = 0;
                    end
                end
                % end %( j == (1 + half_a_boxy))
                if ( i == (1 + half_a_boxx))
                    left_l = -half_a_boxx;
                    right_l = 0;
                else if ( i == (LX - half_a_boxx))
                        left_l = 0;
                        right_l = half_a_boxx;
                else
                    left_l = 0;
                    right_l = 0;
                end
            end


            for (k = left_k:right_k)
                for (l =left_l:right_l)
                    if ((mask(i+l, j+k)>0)) % && (elev(i+l,j+l)>-.0))
                        if ((max_height2 == min_height2) | (length(max_height2)<1))
                            T_down(i+l,j+k) = T(i+l,j+k);
                            lapse(i+l,j+k)=0;
                        else
                            if (length(max_height2)<1)
                                lapse(i+l,j+k)=0;
                                T_down(i+l,j+k) = T(i+l,j+k);
                            else
                                lapse(i+l,j+k)= (min_value - max_value) / (max_height2-min_height2);
                                T_down(i+l,j+k) = T(i+l,j+k) + ...
                                    lapse(i+l,j+k)* (elev(i+l,j+k) - elev2(i+l,j+k));

                            end
                        end
                    else
                        %    T_down(i+l,j+k)=NaN;
                    end
                end
            end %for (k,l)=(left:right)
        end
    end
end
        end

To=T+273.15;
To(find(isnan(T_down)))=NaN;
Tn=T_down+273.15;
oldsum = nanusum(To);
newsum = nanusum(Tn);
sscale = oldsum/newsum
T_down = (Tn*sscale)-273.15;
Tmelt  = 273.15;
T_down(find(~mask))=NaN;
bla='calculating PDD'
PDD_out = PDD4(T_down,stddev);
PDD_in = PDD4(T,stddev);
