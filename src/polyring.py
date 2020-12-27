# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import numpy as np
from numpy.random import randn
from segment import Segment
from point import Point


class JaggedRing:
    @staticmethod
    def __unequalrange(minv, maxv, ndiv, aj_pc):

        values = np.linspace(minv, maxv, ndiv+1)
        equal_div = values[1]-values[0]
        fullring = np.abs(np.diff(np.unwrap([minv, maxv]))) < equal_div
        noise = randn(ndiv+1)*(aj_pc/100 * equal_div)
        noise = np.clip(noise, -equal_div/2, equal_div/2)
        if fullring:
            noise[-1] = -noise[0]
        else:
            noise[0] = 0
            noise[-1] = 0
        return values+noise

    @staticmethod
    def __createloop(dist, ndiv, aj_pc, rj_pc, min_dist_scale, max_dist_scale, skew_angle, max_skew, prev_loop):
        angles = JaggedRing.__unequalrange(0, np.pi*2, ndiv, aj_pc)[0:-1]
        if(skew_angle is None):
            rad_distances = np.clip(
                (randn(ndiv) * rj_pc/100 * dist)+dist, dist*min_dist_scale, dist*max_dist_scale)
        else:
            def skew_coef(angle, skew_angle):
                angle_diff = np.abs(np.diff(np.unwrap([angle, skew_angle])))[0]
                return 0.0 if angle_diff > (np.pi/2) else (1.0 - angle_diff/(np.pi/2))

            def skewed_dist(dist, rj_pc, angle, skew_angle, max_skew, min_dist_scale, max_dist_scale):
                skew_dist = (1+skew_coef(angle, skew_angle)*(max_skew-1))*dist
                return np.clip((randn() * rj_pc/100 * skew_dist)+skew_dist, skew_dist*min_dist_scale, skew_dist*max_dist_scale)
            rad_distances = np.array([skewed_dist(
                dist, rj_pc, angle, skew_angle, max_skew, min_dist_scale, max_dist_scale) for angle in angles])

        if(prev_loop is None):
            radiuses = rad_distances
        else:
            radiuses = np.array(
                [p.r for p in prev_loop.points[:-1]])+rad_distances

        return [Point(r=r, a=a) for r, a in zip(radiuses, angles)]

    @staticmethod
    def __createprojectileloop(dist, ndiv, aj_pc, rj_pc, min_dist_scale, max_dist_scale, skew_angle, max_skew, projectile):
        angles = JaggedRing.__unequalrange(0, np.pi*2, ndiv, aj_pc)[0:-1]
        radialsegs = [Segment(Point(0, 0), Point(
            r=projectile.radius*2, a=a)) for a in angles]
        intersects = [next((seg1.intersectpoint(seg2) for seg2 in projectile.segments(
        ) if seg1.intersects(seg2))) for seg1 in radialsegs]

        return intersects

    def __init__(self, dist, ndiv, aj_pc=30.0, rj_pc=50.0, min_dist_scale=0.1, max_dist_scale=5, skew_angle=None, max_skew=4.0, inner_ring=None, projectile=None):

        self.aj_pc = aj_pc
        self.rj_pc = rj_pc
        if inner_ring is None:
            self.skew_angle = skew_angle
        else:
            self.skew_angle = skew_angle if skew_angle else inner_ring.skew_angle
        self.inner_ring = inner_ring
        if(projectile and not inner_ring):
            self.points = JaggedRing.__createprojectileloop(
                dist, ndiv, aj_pc, rj_pc, min_dist_scale, max_dist_scale, skew_angle, max_skew, projectile)
        else:
            self.points = JaggedRing.__createloop(
                dist, ndiv, aj_pc, rj_pc, min_dist_scale, max_dist_scale, skew_angle, max_skew, inner_ring)
        self.points.append(self.points[0])

    def centeron(self, cp: Point):
        self.points = [cp+p for p in self.points]
        return self
